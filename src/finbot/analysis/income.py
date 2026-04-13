"""Income tracking and aggregation."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from finbot.models.transaction import Transaction


def total_income(session: Session, start: date | None = None, end: date | None = None) -> float:
    q = session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.tx_type == "income"
    )
    if start is not None:
        q = q.filter(Transaction.date >= start)
    if end is not None:
        q = q.filter(Transaction.date <= end)
    return float(q.scalar())


def income_by_month(session: Session) -> dict[str, float]:
    rows = (
        session.query(
            func.strftime("%Y-%m", Transaction.date).label("month"),
            func.sum(Transaction.amount),
        )
        .filter(Transaction.tx_type == "income")
        .group_by("month")
        .order_by("month")
        .all()
    )
    return {r[0]: float(r[1]) for r in rows}


def income_by_category(session: Session, start: date | None = None, end: date | None = None) -> dict[str, float]:
    q = session.query(
        func.coalesce(Transaction.category, "Uncategorized"),
        func.sum(Transaction.amount),
    ).filter(Transaction.tx_type == "income")
    if start:
        q = q.filter(Transaction.date >= start)
    if end:
        q = q.filter(Transaction.date <= end)
    rows = q.group_by(func.coalesce(Transaction.category, "Uncategorized")).all()
    return {r[0]: float(r[1]) for r in rows}
