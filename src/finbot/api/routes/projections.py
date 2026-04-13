"""Growth projection endpoints."""
from fastapi import APIRouter

from finbot.analysis.projections import monte_carlo
from finbot.api.deps import CurrentUser
from finbot.api.schemas import MonteCarloOut, MonteCarloRequest

router = APIRouter(prefix="/api/projections", tags=["projections"])


@router.post("/monte-carlo", response_model=MonteCarloOut)
def run_monte_carlo(body: MonteCarloRequest, _user: CurrentUser):
    result = monte_carlo(body.initial, body.annual_contribution, body.years, inflation=body.inflation)
    return MonteCarloOut(years=result.years, nominal=result.nominal, real=result.real, percentiles=result.percentiles)
