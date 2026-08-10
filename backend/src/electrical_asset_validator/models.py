from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_public_id() -> str:
    return str(uuid4())


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_public_id)
    session_token: Mapped[str] = mapped_column(String(128), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    quality_score: Mapped[float] = mapped_column(Float)
    total_rows: Mapped[int] = mapped_column(Integer)
    valid_rows: Mapped[int] = mapped_column(Integer)
    issue_count: Mapped[int] = mapped_column(Integer)
    returned_issue_count: Mapped[int] = mapped_column(Integer)
    issues_truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    error_count: Mapped[int] = mapped_column(Integer)
    warning_count: Mapped[int] = mapped_column(Integer)
    info_count: Mapped[int] = mapped_column(Integer)
    records: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    source_columns: Mapped[list[str]] = mapped_column(JSON, default=list)

    issues: Mapped[list["ValidationIssue"]] = relationship(
        back_populates="validation",
        cascade="all, delete-orphan",
        order_by="ValidationIssue.id",
    )


class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    validation_id: Mapped[str] = mapped_column(
        ForeignKey("validation_runs.id", ondelete="CASCADE"), index=True
    )
    severity: Mapped[str] = mapped_column(String(10), index=True)
    rule: Mapped[str] = mapped_column(String(64), index=True)
    row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_tag: Mapped[str | None] = mapped_column(Text, nullable=True)
    field: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    validation: Mapped[ValidationRun] = relationship(back_populates="issues")


class ComparisonRun(Base):
    __tablename__ = "comparison_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_public_id)
    session_token: Mapped[str] = mapped_column(String(128), index=True)
    before_filename: Mapped[str] = mapped_column(String(255))
    after_filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    added_count: Mapped[int] = mapped_column(Integer)
    removed_count: Mapped[int] = mapped_column(Integer)
    changed_count: Mapped[int] = mapped_column(Integer)
    unchanged_count: Mapped[int] = mapped_column(Integer)
    added: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    removed: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    changed: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    diffs: Mapped[list["ComparisonDiff"]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
        order_by="ComparisonDiff.id",
    )


class ComparisonDiff(Base):
    __tablename__ = "comparison_diffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comparison_id: Mapped[str] = mapped_column(
        ForeignKey("comparison_runs.id", ondelete="CASCADE"), index=True
    )
    asset_tag: Mapped[str] = mapped_column(String(128), index=True)
    change_type: Mapped[str] = mapped_column(String(16), index=True)
    field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    after_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    comparison: Mapped[ComparisonRun] = relationship(back_populates="diffs")
