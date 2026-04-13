"""Budget endpoints."""
from datetime import date

from fastapi import APIRouter

from finbot.analysis.budget import get_budget_variance, set_budget
from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import BudgetSet, BudgetVarianceOut
from finbot.models.budget import Budget

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("")
def list_budgets(db: DbSession, _user: CurrentUser):
    return [{"category": b.category, "monthly_limit": float(b.monthly_limit), "effective_month": b.effective_month} for b in db.query(Budget).all()]


@router.post("")
def create_budget(body: BudgetSet, db: DbSession, _user: CurrentUser):
    month = body.month or date.today().strftime("%Y-%m")
    b = set_budget(db, body.category, body.monthly_limit, month)
    db.commit()
    return {"id": b.id, "category": b.category, "monthly_limit": float(b.monthly_limit)}


@router.get("/variance", response_model=list[BudgetVarianceOut])
def budget_variance(db: DbSession, _user: CurrentUser, month: str | None = None):
    m = month or date.today().strftime("%Y-%m")
    return [BudgetVarianceOut(category=v.category, budget=v.budget, actual=v.actual, variance=v.variance, pct=v.pct, is_over=v.is_over) for v in get_budget_variance(db, m)]
