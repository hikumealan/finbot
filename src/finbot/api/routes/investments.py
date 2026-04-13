"""Investment analysis endpoints."""
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from finbot.analysis.investments import fee_impact, portfolio_summary
from finbot.analysis.rebalancer import check_rebalance
from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import FeeImpactOut, FeeImpactRequest, PortfolioSummaryOut
from finbot.models.holding import Holding
from finbot.security.audit import create_audit_entry

router = APIRouter(prefix="/api/investments", tags=["investments"])


class HoldingCreate(BaseModel):
    account_id: int
    symbol: str
    shares: float
    cost_basis: float
    current_price: float | None = None
    asset_class: str = "equity"


class HoldingUpdate(BaseModel):
    shares: float | None = None
    cost_basis: float | None = None
    current_price: float | None = None
    asset_class: str | None = None


@router.get("/summary", response_model=PortfolioSummaryOut)
def get_summary(db: DbSession, _user: CurrentUser):
    ps = portfolio_summary(db)
    return PortfolioSummaryOut(**ps.__dict__)


@router.get("/rebalance")
def get_rebalance(db: DbSession, _user: CurrentUser):
    suggestions = check_rebalance(db)
    return [{"asset_class": s.asset_class, "current_pct": s.current_pct, "target_pct": s.target_pct, "drift": s.drift, "action": s.action, "amount": s.amount} for s in suggestions]


@router.post("/fee-impact", response_model=FeeImpactOut)
def calc_fee_impact(body: FeeImpactRequest, _user: CurrentUser):
    result = fee_impact(body.balance, body.expense_ratio, body.years)
    return FeeImpactOut(**result)


@router.get("/holdings")
def list_holdings(db: DbSession, _user: CurrentUser):
    holdings = db.query(Holding).all()
    return [{"id": h.id, "account_id": h.account_id, "symbol": h.symbol, "shares": float(h.shares), "cost_basis": float(h.cost_basis), "current_price": float(h.current_price) if h.current_price else None, "asset_class": h.asset_class} for h in holdings]


@router.post("/holdings")
def create_holding(body: HoldingCreate, db: DbSession, _user: CurrentUser):
    h = Holding(account_id=body.account_id, symbol=body.symbol, shares=body.shares, cost_basis=body.cost_basis, current_price=body.current_price, date=date.today(), asset_class=body.asset_class)
    db.add(h)
    create_audit_entry(db, "create", "holding", details={"symbol": body.symbol})
    db.commit()
    db.refresh(h)
    return {"id": h.id, "symbol": h.symbol}


@router.patch("/holdings/{holding_id}")
def update_holding(holding_id: int, body: HoldingUpdate, db: DbSession, _user: CurrentUser):
    h = db.query(Holding).get(holding_id)
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(h, field, val)
    h.price_as_of = date.today()
    create_audit_entry(db, "edit", "holding", holding_id)
    db.commit()
    return {"status": "updated"}


@router.delete("/holdings/{holding_id}")
def delete_holding(holding_id: int, db: DbSession, _user: CurrentUser):
    h = db.query(Holding).get(holding_id)
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(h)
    create_audit_entry(db, "delete", "holding", holding_id)
    db.commit()
    return {"status": "deleted"}
