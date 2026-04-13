"""Expense aggregation and trends."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from finbot.models.transaction import Transaction


def total_expenses(
    session: Session,
    start: date | None = None,
    end: date | None = None,
    end_exclusive: bool = False,
) -> float:
    q = session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.tx_type == "expense"
    )
    if start is not None:
        q = q.filter(Transaction.date >= start)
    if end is not None:
        q = q.filter(Transaction.date < end) if end_exclusive else q.filter(Transaction.date <= end)
    return abs(float(q.scalar()))


def expenses_by_category(
    session: Session,
    start: date | None = None,
    end: date | None = None,
    end_exclusive: bool = False,
) -> dict[str, float]:
    q = session.query(
        func.coalesce(Transaction.category, "Uncategorized"),
        func.sum(Transaction.amount),
    ).filter(Transaction.tx_type == "expense")
    if start is not None:
        q = q.filter(Transaction.date >= start)
    if end is not None:
        q = q.filter(Transaction.date < end) if end_exclusive else q.filter(Transaction.date <= end)
    rows = q.group_by(func.coalesce(Transaction.category, "Uncategorized")).all()
    return {r[0]: abs(float(r[1])) for r in rows}


def expenses_by_month(session: Session) -> dict[str, float]:
    rows = (
        session.query(
            func.strftime("%Y-%m", Transaction.date).label("month"),
            func.sum(Transaction.amount),
        )
        .filter(Transaction.tx_type == "expense")
        .group_by("month")
        .order_by("month")
        .all()
    )
    return {r[0]: abs(float(r[1])) for r in rows}


def top_merchants(
    session: Session,
    limit: int = 10,
    start: date | None = None,
    end: date | None = None,
) -> list[tuple[str, float]]:
    q = session.query(
        Transaction.description,
        func.sum(Transaction.amount),
    ).filter(Transaction.tx_type == "expense")
    if start is not None:
        q = q.filter(Transaction.date >= start)
    if end is not None:
        q = q.filter(Transaction.date <= end)
    rows = q.group_by(Transaction.description).order_by(func.sum(Transaction.amount)).limit(limit).all()
    return [(r[0], abs(float(r[1]))) for r in rows]
