"""Dashboard summary endpoint."""
from fastapi import APIRouter

from finbot.analysis.expenses import expenses_by_category, expenses_by_month, total_expenses
from finbot.analysis.income import total_income
from finbot.analysis.net_worth import compute_net_worth
from finbot.analysis.savings_rate import overall_savings_rate
from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: DbSession, _user: CurrentUser):
    nw = compute_net_worth(db)
    return DashboardSummary(
        net_worth=nw.net_worth,
        total_assets=nw.total_assets,
        total_liabilities=nw.total_liabilities,
        liquid_savings=nw.liquid_savings,
        emergency_fund_months=nw.emergency_fund_months if nw.emergency_fund_months != float("inf") else -1,
        total_income=total_income(db),
        total_expenses=total_expenses(db),
        savings_rate=overall_savings_rate(db),
        expenses_by_category=expenses_by_category(db),
        expenses_by_month=expenses_by_month(db),
    )
