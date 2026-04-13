"""Statement and tax document import endpoints."""
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile

from finbot.analysis.categorizer import categorize_description
from finbot.api.deps import CurrentUser, DbSession
from finbot.models.account import Account
from finbot.models.audit_log import AuditLog
from finbot.models.holding import Holding
from finbot.models.transaction import Transaction
from finbot.parsers import detect_and_parse
from finbot.parsers.dedup import compute_fingerprint, detect_transfers, find_duplicates
from finbot.security.audit import create_audit_entry

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/statement")
async def import_statement(file: UploadFile, db: DbSession, _user: CurrentUser):
    content = await file.read()
    suffix = Path(file.filename or "file.csv").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content)
        tmp = Path(f.name)

    try:
        result = detect_and_parse(tmp)

        from finbot.config import settings
        settings.ensure_dirs()
        stored_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename or 'file' + suffix}"
        shutil.copy2(tmp, settings.imports_dir / stored_name)
    finally:
        tmp.unlink(missing_ok=True)

    if not result.transactions and not result.holdings:
        return {"status": "empty", "warnings": result.warnings}

    account = db.query(Account).filter_by(
        institution=result.account_institution or "Unknown",
        name=result.account_name or "Primary",
    ).first()
    if not account:
        account = Account(institution=result.account_institution or "Unknown", name=result.account_name or "Primary", account_type=result.account_type or "checking")
        db.add(account)
        db.flush()

    new_txs, dupes = find_duplicates(db, account.id, result.transactions)

    added = 0
    for ptx in new_txs:
        cat, subcat = categorize_description(ptx.description, db)
        if cat and cat.lower() in ("income", "salary", "payroll"):
            ptx.tx_type = "income"
        tx = Transaction(
            account_id=account.id, date=ptx.date, amount=ptx.amount, description=ptx.description,
            category=ptx.category or cat, subcategory=ptx.subcategory or subcat, tx_type=ptx.tx_type,
            fingerprint_hash=compute_fingerprint(account.id, ptx.date, ptx.amount, ptx.description),
            source_file=file.filename,
        )
        db.add(tx)
        added += 1

    from datetime import date as date_cls

    holdings_added = 0
    for ph in result.holdings:
        db.add(Holding(
            account_id=account.id, symbol=ph.symbol, shares=ph.shares, cost_basis=ph.cost_basis,
            current_price=ph.current_price, price_as_of=ph.price_as_of or date_cls.today(),
            date=date_cls.today(), asset_class=ph.asset_class,
        ))
        holdings_added += 1

    transfers = detect_transfers(db)

    create_audit_entry(db, "import", "file", None, {
        "file": file.filename, "transactions_added": added,
        "holdings_added": holdings_added, "duplicates": len(dupes), "transfers_linked": transfers,
    })
    db.commit()

    from finbot.parsers.classifier import classify

    classification = classify(result)

    return {
        "status": "ok", "transactions_added": added, "holdings_added": holdings_added,
        "duplicates_skipped": len(dupes), "transfers_linked": transfers, "warnings": result.warnings,
        **classification,
    }


@router.get("/history")
def import_history(db: DbSession, _user: CurrentUser):
    imports = db.query(AuditLog).filter(AuditLog.action == "import").order_by(AuditLog.timestamp.desc()).limit(50).all()
    result = []
    for imp in imports:
        details = json.loads(imp.details_json) if imp.details_json else {}
        result.append({
            "id": imp.id,
            "file": details.get("file", "unknown"),
            "transactions_added": details.get("transactions_added", details.get("added", 0)),
            "duplicates": details.get("duplicates", 0),
            "timestamp": str(imp.timestamp)[:19],
        })
    return result
