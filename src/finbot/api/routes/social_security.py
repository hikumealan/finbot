"""Social Security estimation and optimization endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from finbot.analysis.social_security import estimate_benefits, optimize_claiming
from finbot.api.deps import CurrentUser

router = APIRouter(prefix="/api/social-security", tags=["social-security"])


class SSEstimateRequest(BaseModel):
    annual_salary: float
    years_worked: int
    birth_year: int | None = None


class SSOptimizeRequest(BaseModel):
    annual_salary: float
    years_worked: int
    current_age: int
    life_expectancy: int = 85
    spouse_salary: float | None = None
    spouse_years_worked: int | None = None
    other_annual_income: float = 0


@router.post("/estimate")
def estimate(body: SSEstimateRequest, _user: CurrentUser):
    estimates = estimate_benefits(body.annual_salary, body.years_worked, body.birth_year)
    return [{"claiming_age": e.claiming_age, "monthly_benefit": e.monthly_benefit, "annual_benefit": e.annual_benefit, "adjustment_pct": e.adjustment_pct} for e in estimates]


@router.post("/optimize")
def optimize(body: SSOptimizeRequest, _user: CurrentUser):
    result = optimize_claiming(
        body.annual_salary, body.years_worked, body.current_age,
        body.life_expectancy, body.spouse_salary, body.spouse_years_worked,
        body.other_annual_income,
    )
    return {
        "estimates": [{"claiming_age": e.claiming_age, "monthly_benefit": e.monthly_benefit, "annual_benefit": e.annual_benefit, "adjustment_pct": e.adjustment_pct} for e in result.estimates],
        "break_even_ages": result.break_even_ages,
        "optimal_age": result.optimal_age,
        "optimal_monthly": result.optimal_monthly,
        "lifetime_benefits": result.lifetime_benefits,
        "recommendation": result.recommendation,
        "spousal_benefit": result.spousal_benefit,
    }
