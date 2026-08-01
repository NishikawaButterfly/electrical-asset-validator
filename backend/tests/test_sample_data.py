from __future__ import annotations

from pathlib import Path

from electrical_asset_validator.services.comparison import compare_datasets
from electrical_asset_validator.services.ingest import parse_dataset
from electrical_asset_validator.services.validation import validate_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA = PROJECT_ROOT / "sample-data"


def _sample(name: str):
    path = SAMPLE_DATA / name
    return parse_dataset(path.name, path.read_bytes())


def test_documented_sample_workflows_remain_reproducible() -> None:
    revision_a = _sample("revision-a.csv")
    revision_b = _sample("revision-b.csv")
    invalid_register = _sample("invalid-register.csv")

    baseline_validation = validate_dataset(revision_a)
    candidate_validation = validate_dataset(revision_b)
    invalid_validation = validate_dataset(invalid_register)
    comparison = compare_datasets(revision_a, revision_b)

    assert baseline_validation.quality_score == 100
    assert baseline_validation.findings == []
    assert candidate_validation.quality_score == 100
    assert candidate_validation.findings == []
    assert invalid_validation.error_count == 7
    assert invalid_validation.warning_count == 5
    assert invalid_validation.quality_score == 58.2
    commissioning_finding = next(
        finding
        for finding in invalid_validation.findings
        if finding.rule == "INVALID_STATUS"
    )
    assert commissioning_finding.suggestion is None
    assert len(comparison.added) == 1
    assert len(comparison.removed) == 1
    assert len(comparison.changed) == 4
    assert comparison.unchanged == 10
