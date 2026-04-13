"""Expense analysis endpoints."""
from datetime import date

from fastapi import APIRouter, Query

from finbot.analysis.expenses import expenses_by_category, expenses_by_month, top_merchants, total_expenses
from finbot.analysis.subscriptions import detect_subscriptions
from finbot.api.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("")
def get_expenses(db: DbSession, _user: CurrentUser, month: str | None = Query(None)):
    start = end = None
    if month:
        y, m = int(month[:4]), int(month[5:7])
        start = date(y, m, 1)
        end = date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)
    return {
        "total": total_expenses(db, start, end),
        "by_category": expenses_by_category(db, start, end),
    }


@router.get("/by-month")
def get_by_month(db: DbSession, _user: CurrentUser):
    return expenses_by_month(db)


@router.get("/top-merchants")
def get_top_merchants(db: DbSession, _user: CurrentUser, limit: int = Query(10)):
    return [{"merchant": m, "amount": a} for m, a in top_merchants(db, limit)]


@router.get("/subscriptions")
def get_subscriptions(db: DbSession, _user: CurrentUser):
    subs = detect_subscriptions(db, min_occurrences=2)
    return [{"description": s.description, "amount": s.amount, "frequency": s.frequency, "category": s.category} for s in subs]
