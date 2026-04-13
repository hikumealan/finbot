"""Recurring charge detection."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from finbot.models.transaction import Transaction


@dataclass
class Subscription:
    description: str
    amount: float
    frequency: int  # how many months it appeared
    category: str | None


def detect_subscriptions(session: Session, min_occurrences: int = 3) -> list[Subscription]:
    """Find recurring charges by matching description + amount across months."""
    rows = (
        session.query(
            Transaction.description,
            Transaction.amount,
            Transaction.category,
            func.count(func.distinct(func.strftime("%Y-%m", Transaction.date))).label("months"),
        )
        .filter(Transaction.tx_type == "expense")
        .group_by(Transaction.description, Transaction.amount)
        .having(func.count(func.distinct(func.strftime("%Y-%m", Transaction.date))) >= min_occurrences)
        .order_by(Transaction.amount)
        .all()
    )

    return [
        Subscription(
            description=r[0],
            amount=abs(float(r[1])),
            frequency=int(r[3]),
            category=r[2],
        )
        for r in rows
    ]


def total_recurring_cost(session: Session) -> float:
    subs = detect_subscriptions(session, min_occurrences=2)
    return sum(s.amount for s in subs)
