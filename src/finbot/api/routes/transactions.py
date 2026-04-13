"""Transaction CRUD endpoints."""
from fastapi import APIRouter, HTTPException, Query

from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import TransactionOut, TransactionUpdate
from finbot.models.transaction import Transaction
from finbot.security.audit import create_audit_entry

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    db: DbSession,
    _user: CurrentUser,
    limit: int = Query(50),
    offset: int = Query(0),
    category: str | None = Query(None),
    tx_type: str | None = Query(None),
):
    q = db.query(Transaction).order_by(Transaction.date.desc())
    if category:
        q = q.filter(Transaction.category == category)
    if tx_type:
        q = q.filter(Transaction.tx_type == tx_type)
    return q.offset(offset).limit(limit).all()


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(tx_id: int, body: TransactionUpdate, db: DbSession, _user: CurrentUser):
    tx = db.query(Transaction).get(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    create_audit_entry(db, "edit", "transaction", tx_id, {"fields": list(body.model_dump(exclude_unset=True).keys())})
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}")
def delete_transaction(tx_id: int, db: DbSession, _user: CurrentUser):
    tx = db.query(Transaction).get(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    create_audit_entry(db, "delete", "transaction", tx_id, {"description": tx.description[:50]})
    db.delete(tx)
    db.commit()
    return {"status": "deleted"}
