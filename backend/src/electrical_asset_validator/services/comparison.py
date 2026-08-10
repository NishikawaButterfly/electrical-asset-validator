from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ingest import CANONICAL_COLUMNS, Dataset, DatasetError
from .validation import (
    ASSET_TAG_PATTERN,
    MAX_ASSET_TAG_CHARACTERS,
    is_blank,
    normalize_asset_tag,
)

MAX_COMPARISON_DETAILS = 10_000


@dataclass(frozen=True)
class ComparisonOutcome:
    added: list[dict[str, Any]]
    removed: list[dict[str, Any]]
    changed: list[dict[str, Any]]
    unchanged: int


def _index_by_tag(dataset: Dataset, label: str) -> dict[str, tuple[int, dict[str, Any]]]:
    missing_columns = [
        column for column in CANONICAL_COLUMNS if column not in dataset.present_columns
    ]
    if missing_columns:
        raise DatasetError(
            f"The {label} file is missing canonical columns: " + ", ".join(missing_columns) + "."
        )

    indexed: dict[str, tuple[int, dict[str, Any]]] = {}
    for row_number, record in zip(
        dataset.row_numbers,
        dataset.records,
        strict=True,
    ):
        raw_tag = record.get("asset_tag")
        if is_blank(raw_tag):
            raise DatasetError(f"The {label} file has a blank asset_tag on row {row_number}.")
        tag = str(raw_tag)
        normalized_tag = normalize_asset_tag(tag)
        if normalized_tag in indexed:
            raise DatasetError(
                f"The {label} file contains duplicate asset_tag '{normalized_tag}'."
            )
        if len(tag) > MAX_ASSET_TAG_CHARACTERS or not ASSET_TAG_PATTERN.fullmatch(tag):
            raise DatasetError(
                f"The {label} file has an invalid asset_tag '{tag}' on row {row_number}."
            )
        normalized_record = dict(record)
        normalized_record["asset_tag"] = tag
        indexed[tag] = (row_number, normalized_record)
    return indexed


def compare_datasets(before: Dataset, after: Dataset) -> ComparisonOutcome:
    before_by_tag = _index_by_tag(before, "before")
    after_by_tag = _index_by_tag(after, "after")

    before_tags = set(before_by_tag)
    after_tags = set(after_by_tag)
    added_tags = sorted(after_tags - before_tags)
    removed_tags = sorted(before_tags - after_tags)
    detail_count = len(added_tags) + len(removed_tags)
    if detail_count > MAX_COMPARISON_DETAILS:
        raise DatasetError(
            "The comparison exceeds the "
            f"{MAX_COMPARISON_DETAILS:,}-detail output limit. "
            "Compare smaller revision segments."
        )
    added = [{"asset_tag": tag, "row": after_by_tag[tag][0]} for tag in added_tags]
    removed = [{"asset_tag": tag, "row": before_by_tag[tag][0]} for tag in removed_tags]

    changed: list[dict[str, Any]] = []
    unchanged = 0
    for tag in sorted(before_tags & after_tags):
        before_record = before_by_tag[tag][1]
        after_record = after_by_tag[tag][1]
        changes = [
            {
                "field": field,
                "before": before_record.get(field),
                "after": after_record.get(field),
            }
            for field in CANONICAL_COLUMNS
            if field != "asset_tag" and before_record.get(field) != after_record.get(field)
        ]
        if changes:
            detail_count += len(changes)
            if detail_count > MAX_COMPARISON_DETAILS:
                raise DatasetError(
                    "The comparison exceeds the "
                    f"{MAX_COMPARISON_DETAILS:,}-detail output limit. "
                    "Compare smaller revision segments."
                )
            changed.append({"asset_tag": tag, "changes": changes})
        else:
            unchanged += 1

    return ComparisonOutcome(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )
