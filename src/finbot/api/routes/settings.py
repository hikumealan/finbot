"""Profile, data management, and PIN endpoints."""
import hashlib
import shutil
from datetime import datetime

from fastapi import APIRouter, HTTPException

from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import ClearRequest, DbStats, PinRequest, ProfileOut, ProfileUpdate
from finbot.config import settings
from finbot.models.account import Account
from finbot.models.audit_log import AuditLog
from finbot.models.budget import Budget
from finbot.models.chat_session import ChatMessage, ChatSession
from finbot.models.debt import Debt
from finbot.models.goal import Goal
from finbot.models.holding import Holding, MuniBondDetail
from finbot.models.prompt_version import PromptVersion
from finbot.models.reference import CategoryRule
from finbot.models.snapshot import Snapshot
from finbot.models.tax_document import TaxDocument, TaxLineItem
from finbot.models.transaction import Transaction
from finbot.models.user_profile import UserProfile
from finbot.security.audit import create_audit_entry

router = APIRouter(prefix="/api/settings", tags=["settings"])

_CLEAR_MAP = {
    "transactions": (Transaction,),
    "snapshots": (Snapshot,),
    "accounts": (Transaction, Holding, MuniBondDetail, Account),
    "holdings": (MuniBondDetail, Holding),
    "tax": (TaxLineItem, TaxDocument),
    "budgets": (Budget,),
    "goals": (Goal,),
    "debts": (Debt,),
    "chats": (ChatMessage, ChatSession),
    "prompts": (PromptVersion,),
    "category_rules": (CategoryRule,),
    "audit": (AuditLog,),
}


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: DbSession, _user: CurrentUser):
    p = db.query(UserProfile).first()
    if not p:
        return ProfileOut(age=None, state_of_residence=None, risk_tolerance=5, retirement_target_age=None, filing_status=None, employer_match_pct=None)
    return ProfileOut.model_validate(p)


@router.patch("/profile", response_model=ProfileOut)
def update_profile(body: ProfileUpdate, db: DbSession, _user: CurrentUser):
    p = db.query(UserProfile).first()
    if not p:
        p = UserProfile()
        db.add(p)
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(p, field, val)
    db.commit()
    db.refresh(p)
    return ProfileOut.model_validate(p)


@router.get("/stats", response_model=DbStats)
def get_stats(db: DbSession, _user: CurrentUser):
    return DbStats(
        accounts=db.query(Account).count(),
        transactions=db.query(Transaction).count(),
        holdings=db.query(Holding).count(),
        tax_documents=db.query(TaxDocument).count(),
        chat_sessions=db.query(ChatSession).count(),
        audit_entries=db.query(AuditLog).count(),
        budgets=db.query(Budget).count(),
        goals=db.query(Goal).count(),
        debts=db.query(Debt).count(),
        snapshots=db.query(Snapshot).count(),
        prompts=db.query(PromptVersion).count(),
        category_rules=db.query(CategoryRule).count(),
    )


@router.post("/clear")
def clear_data(body: ClearRequest, db: DbSession, _user: CurrentUser):
    if "all" in body.targets:
        settings.ensure_dirs()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = settings.backups_dir / f"pre_clear_{ts}.db"
        if settings.db_path.exists():
            shutil.copy2(settings.db_path, backup)
        body.targets = list(_CLEAR_MAP.keys())

    cleared = []
    for target in body.targets:
        models = _CLEAR_MAP.get(target)
        if not models:
            continue
        for model in models:
            db.query(model).delete()
        cleared.append(target)

    if "audit" not in body.targets:
        create_audit_entry(db, "clear", details={"cleared": cleared})
    db.commit()
    return {"cleared": cleared}


@router.post("/pin")
def manage_pin(body: PinRequest, db: DbSession, _user: CurrentUser):
    p = db.query(UserProfile).first()
    if not p:
        p = UserProfile()
        db.add(p)

    if body.pin == "":
        p.pin_hash = None
        db.commit()
        return {"status": "removed"}

    if p.pin_hash and body.current_pin:
        if hashlib.sha256(body.current_pin.encode()).hexdigest() != p.pin_hash:
            raise HTTPException(status_code=400, detail="Current PIN incorrect")

    if len(body.pin) < 4:
        raise HTTPException(status_code=400, detail="PIN must be at least 4 characters")

    p.pin_hash = hashlib.sha256(body.pin.encode()).hexdigest()
    db.commit()
    return {"status": "set"}
