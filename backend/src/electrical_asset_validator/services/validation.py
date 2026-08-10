from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import get_close_matches
from math import isfinite
from typing import Any, Literal

from .ingest import CANONICAL_COLUMNS, Dataset

Severity = Literal["error", "warning", "info"]

ASSET_TAG_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")
CIRCUIT_PATTERN = re.compile(r"^[A-Z0-9]+(?:[-/.][A-Z0-9]+)*$")
ALLOWED_STATUSES = (
    "active",
    "standby",
    "maintenance",
    "decommissioned",
)
ROW_REQUIRED_FIELDS = (
    "asset_tag",
    "asset_name",
    "asset_type",
    "location",
    "voltage_v",
    "power_kw",
    "status",
)
PANEL_TYPE_MARKERS = (
    "panel",
    "switchboard",
    "distribution board",
    "distribution_board",
)
MAX_ELECTRICAL_VALUE = 1_000_000
MAX_ASSET_TAG_CHARACTERS = 128
MAX_FINDINGS = 10_000


@dataclass(frozen=True)
class Finding:
    severity: Severity
    rule: str
    row: int | None
    asset_tag: str | None
    field: str | None
    message: str
    suggestion: str | None = None


class FindingCollector(list[Finding]):
    """Retain a bounded set of actionable findings for one validation."""

    def __init__(self) -> None:
        super().__init__()
        self._truncated = False
        self.total_count = 0
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.error_rows: set[int] = set()
        self.dataset_error = False

    def append(self, finding: Finding) -> None:
        self.total_count += 1
        if finding.severity == "error":
            self.error_count += 1
            if finding.row is None:
                self.dataset_error = True
            else:
                self.error_rows.add(finding.row)
        elif finding.severity == "warning":
            self.warning_count += 1
        else:
            self.info_count += 1

        # Reserve the final slot for a visible truncation notice.
        if len(self) < MAX_FINDINGS - 1:
            super().append(finding)
            return
        self._truncated = True

    def finalize(self) -> None:
        if not self._truncated:
            return
        super().append(
            Finding(
                severity="warning",
                rule="FINDING_LIMIT_REACHED",
                row=None,
                asset_tag=None,
                field=None,
                message=(
                    f"The validation reached the {MAX_FINDINGS:,}-finding output "
                    "limit. Correct the listed findings and run validation again."
                ),
            )
        )


@dataclass(frozen=True)
class ValidationOutcome:
    records: list[dict[str, Any]]
    findings: list[Finding]
    quality_score: float
    total_rows: int
    valid_rows: int
    error_count: int
    warning_count: int
    info_count: int
    returned_issue_count: int
    issues_truncated: bool

    @property
    def issue_count(self) -> int:
        return self.error_count + self.warning_count + self.info_count


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def compact_spaces(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_asset_tag(value: Any) -> str:
    tag = compact_spaces(value).upper()
    tag = re.sub(r"[\s_]+", "-", tag)
    return re.sub(r"-+", "-", tag)


def normalize_circuit(value: Any) -> str:
    circuit = compact_spaces(value).upper()
    circuit = re.sub(r"[\s_]+", "-", circuit)
    return re.sub(r"-+", "-", circuit)


def normalize_category(value: Any) -> str:
    return compact_spaces(value).casefold().replace("-", "_").replace(" ", "_")


def is_panel_asset(asset_type: Any) -> bool:
    if is_blank(asset_type):
        return False
    normalized = compact_spaces(asset_type).casefold()
    return any(marker in normalized for marker in PANEL_TYPE_MARKERS)


def parse_number(value: Any) -> float | None:
    if is_blank(value) or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _add_required_findings(
    dataset: Dataset,
    findings: list[Finding],
) -> None:
    for field in CANONICAL_COLUMNS:
        if field not in dataset.present_columns:
            findings.append(
                Finding(
                    severity="error",
                    rule="MISSING_COLUMN",
                    row=None,
                    asset_tag=None,
                    field=field,
                    message=f"Required column '{field}' is missing.",
                    suggestion=field,
                )
            )
    for field in dataset.unexpected_columns:
        findings.append(
            Finding(
                severity="info",
                rule="UNEXPECTED_COLUMN",
                row=None,
                asset_tag=None,
                field=field,
                message=f"Column '{field}' is not part of the canonical schema.",
                suggestion=None,
            )
        )


def _add_naming_findings(
    records: list[dict[str, Any]],
    row_numbers: list[int],
    findings: list[Finding],
) -> None:
    fields = ("asset_type", "location")
    for field in fields:
        values = [
            compact_spaces(record[field]) for record in records if not is_blank(record.get(field))
        ]
        if not values:
            continue

        variants: dict[str, Counter[str]] = defaultdict(Counter)
        for value in values:
            variants[value.casefold()][value] += 1
        preferred_by_key = {key: counts.most_common(1)[0][0] for key, counts in variants.items()}

        canonical_counts = Counter(value.casefold() for value in values)
        canonical_labels = {key: preferred_by_key[key] for key in canonical_counts}
        common_keys = [key for key, count in canonical_counts.items() if count >= 2]

        for row_number, record in zip(row_numbers, records, strict=True):
            value = record.get(field)
            if is_blank(value):
                continue
            compact = compact_spaces(value)
            key = compact.casefold()
            preferred = preferred_by_key[key]
            if str(value) != preferred:
                findings.append(
                    Finding(
                        severity="warning",
                        rule="NAMING_NORMALIZATION",
                        row=row_number,
                        asset_tag=_display_tag(record),
                        field=field,
                        message=f"Use a consistent spelling for '{field}'.",
                        suggestion=preferred,
                    )
                )
                continue

            if canonical_counts[key] != 1 or not common_keys:
                continue
            candidates = [
                candidate
                for candidate in common_keys
                if candidate != key and candidate[:1] == key[:1]
            ]
            matches = get_close_matches(key, candidates, n=1, cutoff=0.88)
            if matches:
                suggestion = canonical_labels[matches[0]]
                findings.append(
                    Finding(
                        severity="warning",
                        rule="POSSIBLE_TYPO",
                        row=row_number,
                        asset_tag=_display_tag(record),
                        field=field,
                        message=f"'{compact}' may be a typo or naming variant.",
                        suggestion=suggestion,
                    )
                )


def _display_tag(record: dict[str, Any]) -> str | None:
    value = record.get("asset_tag")
    return None if is_blank(value) else str(value)


def validate_dataset(dataset: Dataset) -> ValidationOutcome:
    findings = FindingCollector()
    records = dataset.records
    records_by_row = dict(zip(dataset.row_numbers, records, strict=True))
    _add_required_findings(dataset, findings)

    tag_rows: dict[str, list[int]] = defaultdict(list)
    records_by_tag: dict[str, dict[str, Any]] = {}

    for row_number, record in zip(dataset.row_numbers, records, strict=True):
        asset_tag = _display_tag(record)
        for field in ROW_REQUIRED_FIELDS:
            if is_blank(record.get(field)):
                findings.append(
                    Finding(
                        severity="error",
                        rule="REQUIRED_FIELD",
                        row=row_number,
                        asset_tag=asset_tag,
                        field=field,
                        message=f"'{field}' is required.",
                    )
                )

        if asset_tag is not None:
            normalized_tag = normalize_asset_tag(asset_tag)
            tag_rows[normalized_tag].append(row_number)
            records_by_tag.setdefault(normalized_tag, record)
            if len(asset_tag) > MAX_ASSET_TAG_CHARACTERS:
                findings.append(
                    Finding(
                        severity="error",
                        rule="ASSET_TAG_LENGTH",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="asset_tag",
                        message=(
                            "Asset tags may contain no more than "
                            f"{MAX_ASSET_TAG_CHARACTERS} characters."
                        ),
                    )
                )
            if not ASSET_TAG_PATTERN.fullmatch(asset_tag):
                suggestion = (
                    normalized_tag if ASSET_TAG_PATTERN.fullmatch(normalized_tag) else None
                )
                findings.append(
                    Finding(
                        severity="error",
                        rule="ASSET_TAG_FORMAT",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="asset_tag",
                        message=(
                            "Asset tags must start with a letter and contain only "
                            "uppercase letters, numbers, and hyphens."
                        ),
                        suggestion=suggestion,
                    )
                )

        for field, minimum, inclusive in (
            ("voltage_v", 0, False),
            ("power_kw", 0, True),
        ):
            value = record.get(field)
            if is_blank(value):
                continue
            parsed = parse_number(value)
            if parsed is None:
                findings.append(
                    Finding(
                        severity="error",
                        rule="INVALID_NUMBER",
                        row=row_number,
                        asset_tag=asset_tag,
                        field=field,
                        message=f"'{field}' must be a finite number.",
                    )
                )
                continue
            below_minimum = parsed < minimum if inclusive else parsed <= minimum
            if below_minimum or parsed > MAX_ELECTRICAL_VALUE:
                boundary = "at least 0" if inclusive else "greater than 0"
                findings.append(
                    Finding(
                        severity="error",
                        rule="VALUE_OUT_OF_RANGE",
                        row=row_number,
                        asset_tag=asset_tag,
                        field=field,
                        message=(
                            f"'{field}' must be {boundary} and no greater than "
                            f"{MAX_ELECTRICAL_VALUE:,}."
                        ),
                    )
                )

        status = record.get("status")
        if not is_blank(status):
            normalized_status = normalize_category(status)
            if normalized_status not in ALLOWED_STATUSES:
                matches = get_close_matches(normalized_status, ALLOWED_STATUSES, n=1, cutoff=0.8)
                findings.append(
                    Finding(
                        severity="error",
                        rule="INVALID_STATUS",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="status",
                        message=("Status must be one of: " + ", ".join(ALLOWED_STATUSES) + "."),
                        suggestion=matches[0] if matches else None,
                    )
                )
            elif str(status) != normalized_status:
                findings.append(
                    Finding(
                        severity="warning",
                        rule="NAMING_NORMALIZATION",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="status",
                        message="Use the canonical lowercase status value.",
                        suggestion=normalized_status,
                    )
                )

        for field in ("asset_name", "asset_type", "location"):
            value = record.get(field)
            if not is_blank(value) and str(value) != compact_spaces(value):
                findings.append(
                    Finding(
                        severity="warning",
                        rule="NAMING_NORMALIZATION",
                        row=row_number,
                        asset_tag=asset_tag,
                        field=field,
                        message=f"Remove repeated whitespace from '{field}'.",
                        suggestion=compact_spaces(value),
                    )
                )

    for normalized_tag, row_numbers in tag_rows.items():
        if len(row_numbers) < 2:
            continue
        for row_number in row_numbers:
            record = records_by_row[row_number]
            findings.append(
                Finding(
                    severity="error",
                    rule="DUPLICATE_ASSET_TAG",
                    row=row_number,
                    asset_tag=_display_tag(record),
                    field="asset_tag",
                    message=f"Asset tag '{normalized_tag}' occurs more than once.",
                    suggestion=None,
                )
            )

    circuit_rows: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row_number, record in zip(dataset.row_numbers, records, strict=True):
        asset_tag = _display_tag(record)
        panel_tag = record.get("panel_tag")
        circuit_ref = record.get("circuit_ref")
        panel_asset = is_panel_asset(record.get("asset_type"))
        decommissioned = normalize_category(record.get("status")) == "decommissioned"

        if not panel_asset and not decommissioned:
            if is_blank(panel_tag):
                findings.append(
                    Finding(
                        severity="warning",
                        rule="MISSING_PANEL_REFERENCE",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="panel_tag",
                        message="A non-panel asset should reference its supplying panel.",
                    )
                )
            if is_blank(circuit_ref):
                findings.append(
                    Finding(
                        severity="warning",
                        rule="MISSING_CIRCUIT_REFERENCE",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="circuit_ref",
                        message="A non-panel asset should reference its supplying circuit.",
                    )
                )

        normalized_panel: str | None = None
        if not is_blank(panel_tag):
            normalized_panel = normalize_asset_tag(panel_tag)
            if not ASSET_TAG_PATTERN.fullmatch(str(panel_tag)):
                suggestion = (
                    normalized_panel if ASSET_TAG_PATTERN.fullmatch(normalized_panel) else None
                )
                findings.append(
                    Finding(
                        severity="warning",
                        rule="ASSET_TAG_FORMAT",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="panel_tag",
                        message="Panel references must use the canonical asset-tag format.",
                        suggestion=suggestion,
                    )
                )
            target = records_by_tag.get(normalized_panel)
            if target is None:
                findings.append(
                    Finding(
                        severity="warning",
                        rule="UNKNOWN_PANEL_REFERENCE",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="panel_tag",
                        message=f"Panel '{normalized_panel}' is not present in this register.",
                    )
                )
            else:
                if not is_panel_asset(target.get("asset_type")):
                    findings.append(
                        Finding(
                            severity="warning",
                            rule="INVALID_PANEL_REFERENCE",
                            row=row_number,
                            asset_tag=asset_tag,
                            field="panel_tag",
                            message=(
                                f"Referenced asset '{normalized_panel}' is not classified "
                                "as a panel."
                            ),
                        )
                    )
                source_location = record.get("location")
                target_location = target.get("location")
                if (
                    not is_blank(source_location)
                    and not is_blank(target_location)
                    and compact_spaces(source_location).casefold()
                    != compact_spaces(target_location).casefold()
                ):
                    findings.append(
                        Finding(
                            severity="warning",
                            rule="PANEL_LOCATION_MISMATCH",
                            row=row_number,
                            asset_tag=asset_tag,
                            field="panel_tag",
                            message=(
                                f"Asset location differs from panel '{normalized_panel}' location."
                            ),
                            suggestion=str(target_location),
                        )
                    )

        if not is_blank(circuit_ref):
            normalized_circuit = normalize_circuit(circuit_ref)
            if not CIRCUIT_PATTERN.fullmatch(str(circuit_ref)):
                suggestion = (
                    normalized_circuit if CIRCUIT_PATTERN.fullmatch(normalized_circuit) else None
                )
                findings.append(
                    Finding(
                        severity="warning",
                        rule="CIRCUIT_REFERENCE_FORMAT",
                        row=row_number,
                        asset_tag=asset_tag,
                        field="circuit_ref",
                        message=(
                            "Circuit references may contain uppercase letters, numbers, "
                            "hyphens, slashes, and periods."
                        ),
                        suggestion=suggestion,
                    )
                )
            if normalized_panel is not None and not decommissioned:
                circuit_rows[(normalized_panel, normalized_circuit)].append(row_number)

    for (panel_tag, circuit_ref), row_numbers in circuit_rows.items():
        if len(row_numbers) < 2:
            continue
        for row_number in row_numbers:
            record = records_by_row[row_number]
            findings.append(
                Finding(
                    severity="warning",
                    rule="DUPLICATE_CIRCUIT_REFERENCE",
                    row=row_number,
                    asset_tag=_display_tag(record),
                    field="circuit_ref",
                    message=(
                        f"Circuit '{circuit_ref}' on panel '{panel_tag}' is assigned "
                        "to multiple active assets."
                    ),
                )
            )

    _add_naming_findings(records, dataset.row_numbers, findings)
    findings.finalize()

    error_rows = findings.error_rows
    dataset_error = findings.dataset_error
    total_rows = len(records)
    valid_rows = 0 if dataset_error else total_rows - len(error_rows)
    error_count = findings.error_count
    warning_count = findings.warning_count
    info_count = findings.info_count
    if dataset_error:
        quality_score = 0.0
    else:
        penalty = error_count * 8 + warning_count * 3
        maximum_penalty = max(10, total_rows * 10)
        quality_score = round(
            max(0.0, 100.0 - penalty * 100 / maximum_penalty),
            1,
        )
        if error_count or warning_count:
            quality_score = min(quality_score, 99.9)

    return ValidationOutcome(
        records=records,
        findings=findings,
        quality_score=quality_score,
        total_rows=total_rows,
        valid_rows=valid_rows,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        returned_issue_count=len(findings),
        issues_truncated=findings._truncated,
    )
