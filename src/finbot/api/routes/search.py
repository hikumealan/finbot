"""Cross-table search endpoint."""
from fastapi import APIRouter, Query

from finbot.api.deps import CurrentUser, DbSession
from finbot.models.account import Account
from finbot.models.chat_session import ChatSession
from finbot.models.tax_document import TaxDocument
from finbot.models.transaction import Transaction

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(q: str = Query(..., min_length=2), db: DbSession = None, _user: CurrentUser = None):
    """Search across transactions, accounts, tax documents, and chat sessions."""
    results = []
    pattern = f"%{q}%"

    txs = db.query(Transaction).filter(Transaction.description.ilike(pattern)).limit(10).all()
    for tx in txs:
        results.append({"type": "transaction", "id": tx.id, "title": tx.description, "subtitle": f"{tx.date} | ${float(tx.amount):,.2f}", "path": "/expenses"})

    accts = db.query(Account).filter((Account.name.ilike(pattern)) | (Account.institution.ilike(pattern))).limit(5).all()
    for a in accts:
        results.append({"type": "account", "id": a.id, "title": f"{a.institution} - {a.name}", "subtitle": a.account_type, "path": "/settings"})

    docs = db.query(TaxDocument).filter(TaxDocument.source_file.ilike(pattern)).limit(5).all()
    for d in docs:
        results.append({"type": "tax_document", "id": d.id, "title": d.source_file or f"{d.doc_type} {d.tax_year}", "subtitle": f"{d.doc_type} - {d.tax_year}", "path": "/tax"})

    chats = db.query(ChatSession).filter(ChatSession.title.ilike(pattern)).limit(5).all()
    for c in chats:
        results.append({"type": "chat", "id": c.id, "title": c.title or f"Chat #{c.id}", "subtitle": c.advisor_type, "path": "/advisor"})

    return results
