from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["error", "warning", "info"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    database: Literal["ok"]


class IssueResponse(BaseModel):
    id: str
    severity: Severity
    rule: str
    row: int | None
    asset_tag: str | None
    field: str | None
    message: str
    suggestion: str | None


class ValidationMetrics(BaseModel):
    total_rows: int
    valid_rows: int
    issue_count: int
    returned_issue_count: int
    issues_truncated: bool
    error_count: int
    warning_count: int
    info_count: int


class DownloadUrls(BaseModel):
    excel: str
    pdf: str


class ValidationResponse(BaseModel):
    id: str
    filename: str
    created_at: datetime
    quality_score: float = Field(ge=0, le=100)
    metrics: ValidationMetrics
    issues: list[IssueResponse]
    download_urls: DownloadUrls


class ValidationHistoryItem(BaseModel):
    id: str
    filename: str
    created_at: datetime
    quality_score: float
    metrics: ValidationMetrics


class ValidationHistoryResponse(BaseModel):
    items: list[ValidationHistoryItem]
    total: int
    limit: int
    offset: int


class ComparisonSummary(BaseModel):
    added: int
    removed: int
    changed: int
    unchanged: int


class AssetSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_tag: str
    row: int = Field(ge=2)


class FieldChange(BaseModel):
    field: str
    before: Any | None
    after: Any | None


class ChangedAsset(BaseModel):
    asset_tag: str
    changes: list[FieldChange]


class ComparisonResponse(BaseModel):
    id: str
    before_filename: str
    after_filename: str
    created_at: datetime
    summary: ComparisonSummary
    added: list[AssetSnapshot]
    removed: list[AssetSnapshot]
    changed: list[ChangedAsset]


class InspectedColumn(BaseModel):
    header: str
    canonical_field: str | None


class InspectionResponse(BaseModel):
    filename: str
    columns: list[InspectedColumn]
    unmatched_canonical_fields: list[str]
