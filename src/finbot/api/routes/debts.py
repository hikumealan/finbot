"""Debt management endpoints."""
from fastapi import APIRouter, HTTPException, Query

from finbot.analysis.debts import compare_strategies
from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import DebtCreate, DebtOut
from finbot.models.debt import Debt

router = APIRouter(prefix="/api/debts", tags=["debts"])


@router.get("", response_model=list[DebtOut])
def list_debts(db: DbSession, _user: CurrentUser):
    return db.query(Debt).all()


@router.post("", response_model=DebtOut)
def create_debt(body: DebtCreate, db: DbSession, _user: CurrentUser):
    d = Debt(**body.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.patch("/{debt_id}", response_model=DebtOut)
def update_debt(debt_id: int, body: DebtCreate, db: DbSession, _user: CurrentUser):
    d = db.query(Debt).get(debt_id)
    if not d:
        raise HTTPException(status_code=404, detail="Debt not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(d, field, val)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{debt_id}")
def delete_debt(debt_id: int, db: DbSession, _user: CurrentUser):
    d = db.query(Debt).get(debt_id)
    if not d:
        raise HTTPException(status_code=404, detail="Debt not found")
    db.delete(d)
    db.commit()
    return {"status": "deleted"}


@router.get("/compare")
def compare(db: DbSession, _user: CurrentUser, extra_payment: float = Query(0)):
    comp = compare_strategies(db, extra_payment)
    return {
        "avalanche": [{"name": r.name, "months": r.months_to_payoff, "interest": r.total_interest, "total_paid": r.total_paid} for r in comp.avalanche],
        "snowball": [{"name": r.name, "months": r.months_to_payoff, "interest": r.total_interest, "total_paid": r.total_paid} for r in comp.snowball],
        "avalanche_total_interest": comp.avalanche_total_interest,
        "snowball_total_interest": comp.snowball_total_interest,
        "interest_saved": comp.interest_saved,
    }
