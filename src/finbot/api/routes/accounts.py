"""Account management endpoints."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import func

from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import AccountCreate, AccountOut, AccountUpdate, MergeRequest
from finbot.models.account import Account
from finbot.models.holding import Holding
from finbot.models.transaction import Transaction
from finbot.security.audit import create_audit_entry

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(db: DbSession, _user: CurrentUser):
    accounts = db.query(Account).all()
    result = []
    for a in accounts:
        tx_count = db.query(Transaction).filter_by(account_id=a.id).count()
        last = db.query(func.max(Transaction.date)).filter_by(account_id=a.id).scalar()
        result.append(AccountOut(
            id=a.id, institution=a.institution, name=a.name,
            account_type=a.account_type, currency=a.currency,
            is_tax_advantaged=a.is_tax_advantaged,
            transaction_count=tx_count, last_activity=str(last) if last else None,
        ))
    return result


@router.post("", response_model=AccountOut)
def create_account(body: AccountCreate, db: DbSession, _user: CurrentUser):
    a = Account(institution=body.institution, name=body.name, account_type=body.account_type, is_tax_advantaged=body.is_tax_advantaged)
    db.add(a)
    db.commit()
    db.refresh(a)
    return AccountOut(id=a.id, institution=a.institution, name=a.name, account_type=a.account_type, currency=a.currency, is_tax_advantaged=a.is_tax_advantaged)


@router.patch("/{acct_id}", response_model=AccountOut)
def update_account(acct_id: int, body: AccountUpdate, db: DbSession, _user: CurrentUser):
    a = db.query(Account).get(acct_id)
    if not a:
        raise HTTPException(status_code=404, detail="Account not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(a, field, val)
    create_audit_entry(db, "edit", "account", acct_id)
    db.commit()
    db.refresh(a)
    return AccountOut(id=a.id, institution=a.institution, name=a.name, account_type=a.account_type, currency=a.currency, is_tax_advantaged=a.is_tax_advantaged)


@router.delete("/{acct_id}")
def delete_account(acct_id: int, db: DbSession, _user: CurrentUser):
    a = db.query(Account).get(acct_id)
    if not a:
        raise HTTPException(status_code=404, detail="Account not found")
    db.query(Transaction).filter_by(account_id=acct_id).delete()
    db.query(Holding).filter_by(account_id=acct_id).delete()
    db.delete(a)
    create_audit_entry(db, "delete", "account", acct_id)
    db.commit()
    return {"status": "deleted"}


@router.post("/merge")
def merge_accounts(body: MergeRequest, db: DbSession, _user: CurrentUser):
    if body.source_id == body.target_id:
        raise HTTPException(status_code=400, detail="Cannot merge an account into itself")
    db.query(Transaction).filter_by(account_id=body.source_id).update({"account_id": body.target_id})
    db.query(Holding).filter_by(account_id=body.source_id).update({"account_id": body.target_id})
    db.query(Account).filter_by(id=body.source_id).delete()
    create_audit_entry(db, "merge", "account", details={"source": body.source_id, "target": body.target_id})
    db.commit()
    return {"status": "merged"}
