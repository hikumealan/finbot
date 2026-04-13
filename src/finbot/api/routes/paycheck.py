"""Paycheck analysis and what-if comparison endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from finbot.analysis.paycheck import analyze_paycheck, compare_paychecks
from finbot.api.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/paycheck", tags=["paycheck"])


class PaycheckRequest(BaseModel):
    gross_salary: float
    pay_frequency: str = "biweekly"
    filing_status: str = "single"
    state: str | None = None
    k401_pct: float = 0
    hsa_annual: float = 0
    insurance_annual: float = 0


class PaycheckCompareRequest(BaseModel):
    current: PaycheckRequest
    proposed: PaycheckRequest


@router.post("/analyze")
def analyze(body: PaycheckRequest, db: DbSession, _user: CurrentUser):
    result = analyze_paycheck(
        gross_salary=body.gross_salary, pay_frequency=body.pay_frequency,
        filing_status=body.filing_status, state=body.state,
        k401_pct=body.k401_pct, hsa_annual=body.hsa_annual,
        insurance_annual=body.insurance_annual, session=db,
    )
    return {
        "lines": [{"label": line.label, "annual": line.annual, "per_period": line.per_period, "pct_of_gross": line.pct_of_gross} for line in result.all_lines],
        "effective_tax_rate": result.effective_tax_rate,
    }


@router.post("/compare")
def compare(body: PaycheckCompareRequest, db: DbSession, _user: CurrentUser):
    return compare_paychecks(body.current.model_dump(), body.proposed.model_dump(), session=db)
