"""Data export endpoints."""
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from finbot.api.deps import CurrentUser, DbSession
from finbot.export.csv_export import export_holdings, export_tax_data, export_transactions
from finbot.export.pdf_report import generate_report_text

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/transactions")
def export_txs(db: DbSession, _user: CurrentUser):
    return PlainTextResponse(export_transactions(db), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=finbot_transactions.csv"})


@router.get("/holdings")
def export_hold(db: DbSession, _user: CurrentUser):
    return PlainTextResponse(export_holdings(db), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=finbot_holdings.csv"})


@router.get("/tax")
def export_tax(db: DbSession, _user: CurrentUser):
    return PlainTextResponse(export_tax_data(db), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=finbot_tax_data.csv"})


@router.get("/report")
def export_report(db: DbSession, _user: CurrentUser, period: str = Query("Summary")):
    text = generate_report_text(db, period)
    return PlainTextResponse(text, media_type="text/markdown", headers={"Content-Disposition": "attachment; filename=finbot_report.md"})
