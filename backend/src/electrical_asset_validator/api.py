from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from .config import Settings
from .database import get_session
from .models import (
    ComparisonDiff,
    ComparisonRun,
    ValidationIssue,
    ValidationRun,
)
from .schemas import (
    AssetSnapshot,
    ChangedAsset,
    ComparisonResponse,
    ComparisonSummary,
    DownloadUrls,
    FieldChange,
    HealthResponse,
    IssueResponse,
    ValidationHistoryItem,
    ValidationMetrics,
    ValidationResponse,
)
from .services.comparison import compare_datasets
from .services.ingest import DatasetError, parse_dataset
from .services.reports import build_excel_report, build_pdf_report
from .services.validation import validate_dataset

router = APIRouter()


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _read_upload(upload: UploadFile, settings: Settings) -> bytes:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="An uploaded filename is required.")
    maximum_bytes = settings.max_upload_mb * 1024 * 1024
    content = upload.file.read(maximum_bytes + 1)
    if len(content) > maximum_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Each file must be no larger than {settings.max_upload_mb} MB.",
        )
    return content


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _safe_filename(filename: str | None, fallback: str) -> str:
    candidate = (filename or "").replace("\\", "/")
    name = Path(candidate).name.strip()[:255]
    return name or fallback


def _metrics(validation: ValidationRun) -> ValidationMetrics:
    return ValidationMetrics(
        total_rows=validation.total_rows,
        valid_rows=validation.valid_rows,
        issue_count=validation.issue_count,
        returned_issue_count=validation.returned_issue_count,
        issues_truncated=validation.issues_truncated,
        error_count=validation.error_count,
        warning_count=validation.warning_count,
        info_count=validation.info_count,
    )


def _validation_response(
    validation: ValidationRun,
    api_prefix: str = "/api/v1",
) -> ValidationResponse:
    route_prefix = "/" + api_prefix.strip("/")
    return ValidationResponse(
        id=validation.id,
        filename=validation.filename,
        created_at=_utc_datetime(validation.created_at),
        quality_score=validation.quality_score,
        metrics=_metrics(validation),
        issues=[
            IssueResponse(
                id=str(issue.id),
                severity=issue.severity,  # type: ignore[arg-type]
                rule=issue.rule,
                row=issue.row_number,
                asset_tag=issue.asset_tag,
                field=issue.field,
                message=issue.message,
                suggestion=issue.suggestion,
            )
            for issue in validation.issues
        ],
        download_urls=DownloadUrls(
            excel=f"{route_prefix}/validations/{validation.id}/report.xlsx",
            pdf=f"{route_prefix}/validations/{validation.id}/report.pdf",
        ),
    )


def _history_item(validation: ValidationRun) -> ValidationHistoryItem:
    return ValidationHistoryItem(
        id=validation.id,
        filename=validation.filename,
        created_at=_utc_datetime(validation.created_at),
        quality_score=validation.quality_score,
        metrics=_metrics(validation),
    )


def _comparison_response(comparison: ComparisonRun) -> ComparisonResponse:
    return ComparisonResponse(
        id=comparison.id,
        before_filename=comparison.before_filename,
        after_filename=comparison.after_filename,
        created_at=_utc_datetime(comparison.created_at),
        summary=ComparisonSummary(
            added=comparison.added_count,
            removed=comparison.removed_count,
            changed=comparison.changed_count,
            unchanged=comparison.unchanged_count,
        ),
        added=[AssetSnapshot.model_validate(item) for item in comparison.added],
        removed=[AssetSnapshot.model_validate(item) for item in comparison.removed],
        changed=[
            ChangedAsset(
                asset_tag=item["asset_tag"],
                changes=[
                    FieldChange.model_validate(change)
                    for change in item.get("changes", [])
                ],
            )
            for item in comparison.changed
        ],
    )


def _load_validation(session: Session, validation_id: str) -> ValidationRun:
    validation = session.scalar(
        select(ValidationRun)
        .options(selectinload(ValidationRun.issues))
        .where(ValidationRun.id == validation_id)
    )
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found.")
    return validation


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(
    request: Request,
    session: Session = Depends(get_session),
) -> HealthResponse:
    session.execute(text("SELECT 1"))
    settings = _settings(request)
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        database="ok",
    )


@router.post(
    "/validations",
    response_model=ValidationResponse,
    status_code=201,
    tags=["validations"],
)
def create_validation(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ValidationResponse:
    settings = _settings(request)
    content = _read_upload(file, settings)
    try:
        dataset = parse_dataset(file.filename or "", content)
    except DatasetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    outcome = validate_dataset(dataset)
    validation = ValidationRun(
        filename=_safe_filename(file.filename, "upload"),
        quality_score=outcome.quality_score,
        total_rows=outcome.total_rows,
        valid_rows=outcome.valid_rows,
        issue_count=outcome.issue_count,
        returned_issue_count=outcome.returned_issue_count,
        issues_truncated=outcome.issues_truncated,
        error_count=outcome.error_count,
        warning_count=outcome.warning_count,
        info_count=outcome.info_count,
        records=outcome.records,
        source_columns=dataset.source_columns,
    )
    validation.issues = [
        ValidationIssue(
            severity=finding.severity,
            rule=finding.rule,
            row_number=finding.row,
            asset_tag=finding.asset_tag,
            field=finding.field,
            message=finding.message,
            suggestion=finding.suggestion,
        )
        for finding in outcome.findings
    ]
    session.add(validation)
    session.commit()
    return _validation_response(validation, settings.api_prefix)


@router.get(
    "/validations",
    response_model=list[ValidationHistoryItem],
    tags=["validations"],
)
def list_validations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[ValidationHistoryItem]:
    validations = session.scalars(
        select(ValidationRun)
        .order_by(ValidationRun.created_at.desc(), ValidationRun.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [_history_item(validation) for validation in validations]


@router.get(
    "/validations/{validation_id}",
    response_model=ValidationResponse,
    tags=["validations"],
)
def get_validation(
    request: Request,
    validation_id: str,
    session: Session = Depends(get_session),
) -> ValidationResponse:
    return _validation_response(
        _load_validation(session, validation_id),
        _settings(request).api_prefix,
    )


@router.get(
    "/validations/{validation_id}/report.xlsx",
    response_class=StreamingResponse,
    tags=["reports"],
)
def download_excel_report(
    validation_id: str,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    validation = _load_validation(session, validation_id)
    report = build_excel_report(validation)
    return StreamingResponse(
        BytesIO(report),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="validation-{validation.id}.xlsx"'
            )
        },
    )


@router.get(
    "/validations/{validation_id}/report.pdf",
    response_class=StreamingResponse,
    tags=["reports"],
)
def download_pdf_report(
    validation_id: str,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    validation = _load_validation(session, validation_id)
    report = build_pdf_report(validation)
    return StreamingResponse(
        BytesIO(report),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="validation-{validation.id}.pdf"'
            )
        },
    )


@router.post(
    "/comparisons",
    response_model=ComparisonResponse,
    status_code=201,
    tags=["comparisons"],
)
def create_comparison(
    request: Request,
    before_file: UploadFile = File(...),
    after_file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ComparisonResponse:
    settings = _settings(request)
    before_content = _read_upload(before_file, settings)
    after_content = _read_upload(after_file, settings)
    try:
        before_dataset = parse_dataset(before_file.filename or "", before_content)
        after_dataset = parse_dataset(after_file.filename or "", after_content)
        outcome = compare_datasets(before_dataset, after_dataset)
    except DatasetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    comparison = ComparisonRun(
        before_filename=_safe_filename(before_file.filename, "before"),
        after_filename=_safe_filename(after_file.filename, "after"),
        added_count=len(outcome.added),
        removed_count=len(outcome.removed),
        changed_count=len(outcome.changed),
        unchanged_count=outcome.unchanged,
        added=outcome.added,
        removed=outcome.removed,
        changed=outcome.changed,
    )
    for item in outcome.added:
        comparison.diffs.append(
            ComparisonDiff(
                asset_tag=item["asset_tag"],
                change_type="added",
                field=None,
                before_value=None,
                after_value=item["row"],
            )
        )
    for item in outcome.removed:
        comparison.diffs.append(
            ComparisonDiff(
                asset_tag=item["asset_tag"],
                change_type="removed",
                field=None,
                before_value=item["row"],
                after_value=None,
            )
        )
    for item in outcome.changed:
        for change in item["changes"]:
            comparison.diffs.append(
                ComparisonDiff(
                    asset_tag=item["asset_tag"],
                    change_type="changed",
                    field=change["field"],
                    before_value=change["before"],
                    after_value=change["after"],
                )
            )

    session.add(comparison)
    session.commit()
    return _comparison_response(comparison)


@router.get(
    "/comparisons/{comparison_id}",
    response_model=ComparisonResponse,
    tags=["comparisons"],
)
def get_comparison(
    comparison_id: str,
    session: Session = Depends(get_session),
) -> ComparisonResponse:
    comparison = session.get(ComparisonRun, comparison_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Comparison not found.")
    return _comparison_response(comparison)
