from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_session
from .models import ComparisonRun, ValidationRun, utc_now


def sweep_expired(
    session: Session,
    retention_minutes: int,
    now: datetime | None = None,
) -> int:
    """Delete runs older than the retention window; return how many.

    A non-positive ``retention_minutes`` disables the sweep. Deletion goes
    through the ORM so the issue and diff children are removed with their
    parent runs regardless of whether the database enforces foreign keys
    (SQLite does not by default).
    """
    if retention_minutes <= 0:
        return 0
    cutoff = (now or utc_now()) - timedelta(minutes=retention_minutes)
    removed = 0
    for expired in session.scalars(select(ValidationRun).where(ValidationRun.created_at < cutoff)):
        session.delete(expired)
        removed += 1
    for expired in session.scalars(select(ComparisonRun).where(ComparisonRun.created_at < cutoff)):
        session.delete(expired)
        removed += 1
    if removed:
        session.commit()
    return removed


def enforce_retention(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    """Router dependency: sweep before any API request touches the data.

    There is no background scheduler; expiry is enforced lazily on the next
    request, and the deployment's health checks keep that frequent enough.
    """
    settings = request.app.state.settings
    sweep_expired(session, settings.demo_retention_minutes)
