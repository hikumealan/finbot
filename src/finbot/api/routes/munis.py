"""Municipal bond analysis endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from finbot.analysis.muni_bonds import analyze_muni_holdings, quick_tey
from finbot.analysis.tax_optimizer import compute_tax_position
from finbot.api.deps import CurrentUser, DbSession
from finbot.models.holding import Holding, MuniBondDetail
from finbot.models.user_profile import UserProfile

router = APIRouter(prefix="/api/munis", tags=["munis"])


class TEYRequest(BaseModel):
    coupon: float
    federal_rate: float
    state_rate: float = 0
    in_state: bool = True


@router.get("/holdings")
def get_holdings(db: DbSession, _user: CurrentUser):
    profile = db.query(UserProfile).first()
    state = profile.state_of_residence if profile else None
    filing = profile.filing_status if profile else "single"
    pos = compute_tax_position(db, filing, state)
    holdings = analyze_muni_holdings(db, pos.federal_marginal_rate, state)
    return [{"symbol": h.symbol, "coupon_rate": h.coupon_rate, "tey": h.tey, "is_in_state": h.is_in_state, "is_state_exempt": h.is_state_exempt, "credit_rating": h.credit_rating, "is_amt_subject": h.is_amt_subject} for h in holdings]


@router.post("/tey")
def calc_tey(body: TEYRequest, _user: CurrentUser):
    tey = quick_tey(body.coupon, body.federal_rate, body.state_rate, body.in_state)
    return {"coupon": body.coupon, "tey": tey, "combined_rate": body.federal_rate + body.state_rate}


class MuniDetailUpdate(BaseModel):
    issuer_state: str | None = None
    coupon_rate: float | None = None
    credit_rating: str | None = None
    is_amt_subject: bool | None = None
    is_callable: bool | None = None
    bond_type: str | None = None


@router.patch("/{holding_id}")
def update_muni_detail(holding_id: int, body: MuniDetailUpdate, db: DbSession, _user: CurrentUser):
    holding = db.query(Holding).get(holding_id)
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    detail = db.query(MuniBondDetail).filter_by(holding_id=holding_id).first()
    if not detail:
        detail = MuniBondDetail(holding_id=holding_id)
        db.add(detail)

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(detail, field, val)

    holding.asset_class = "muni_bond"
    db.commit()
    return {"status": "updated"}
