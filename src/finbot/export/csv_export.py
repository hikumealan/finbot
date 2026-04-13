"""Export financial data as CSV."""
from __future__ import annotations

import csv
import io
from datetime import date

from sqlalchemy.orm import Session

from finbot.models.holding import Holding
from finbot.models.tax_document import TaxDocument, TaxLineItem
from finbot.models.transaction import Transaction


def export_transactions(
    session: Session,
    start: date | None = None,
    end: date | None = None,
) -> str:
    q = session.query(Transaction).order_by(Transaction.date)
    if start:
        q = q.filter(Transaction.date >= start)
    if end:
        q = q.filter(Transaction.date <= end)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Amount", "Description", "Category", "Subcategory", "Type", "Account ID", "Source"])
    for tx in q.all():
        writer.writerow([
            tx.date.isoformat(), float(tx.amount), tx.description,
            tx.category or "", tx.subcategory or "", tx.tx_type,
            tx.account_id, tx.source_file or "",
        ])
    return buf.getvalue()


def export_holdings(session: Session) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Symbol", "Shares", "Cost Basis", "Current Price", "Price As Of", "Asset Class", "Account ID"])
    for h in session.query(Holding).all():
        writer.writerow([
            h.symbol, float(h.shares), float(h.cost_basis),
            float(h.current_price) if h.current_price else "",
            h.price_as_of.isoformat() if h.price_as_of else "",
            h.asset_class, h.account_id,
        ])
    return buf.getvalue()


def export_tax_data(session: Session) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Tax Year", "Doc Type", "Field Key", "Field Label", "Value", "Source File"])
    docs = session.query(TaxDocument).order_by(TaxDocument.tax_year).all()
    for doc in docs:
        items = session.query(TaxLineItem).filter_by(tax_document_id=doc.id).all()
        for item in items:
            writer.writerow([
                doc.tax_year, doc.doc_type, item.field_key,
                item.field_label or "", item.value, doc.source_file or "",
            ])
    return buf.getvalue()
