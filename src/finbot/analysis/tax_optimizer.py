"""Tax optimization: bracket calculation, TLH, contribution room."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from finbot.models.holding import Holding
from finbot.models.reference import FederalTaxBracket, StateTaxRule
from finbot.models.tax_document import TaxDocument, TaxLineItem
from finbot.models.transaction import Transaction

_STANDARD_DEDUCTION_2025 = {
    "single": 15000,
    "married_joint": 30000,
    "married_separate": 15000,
    "head_of_household": 22500,
}


@dataclass
class TaxPosition:
    gross_income: float
    taxable_income: float
    standard_deduction: float
    federal_tax: float
    federal_effective_rate: float
    federal_marginal_rate: float
    state_tax: float
    state_rate: float
    combined_marginal_rate: float
    total_tax: float
    effective_rate: float


@dataclass
class TLHCandidate:
    symbol: str
    cost_basis: float
    current_value: float
    unrealized_loss: float
    in_wash_window: bool


def compute_tax_position(
    session: Session,
    filing_status: str = "single",
    state_code: str | None = None,
    tax_year: int = 2025,
) -> TaxPosition:
    w2_docs = session.query(TaxDocument).filter_by(doc_type="W2", tax_year=tax_year).all()
    gross_income = 0.0
    for doc in w2_docs:
        box1 = session.query(TaxLineItem).filter_by(
            tax_document_id=doc.id, field_key="box_1"
        ).first()
        if box1:
            try:
                gross_income += float(box1.value)
            except ValueError:
                pass

    std_deduction = _STANDARD_DEDUCTION_2025.get(filing_status, 15000)
    taxable_income = max(0, gross_income - std_deduction)

    brackets = (
        session.query(FederalTaxBracket)
        .filter_by(tax_year=tax_year, filing_status=filing_status)
        .order_by(FederalTaxBracket.bracket_floor)
        .all()
    )

    federal_tax = 0.0
    marginal_rate = 0.10
    remaining = taxable_income
    for bracket in brackets:
        floor = float(bracket.bracket_floor)
        ceiling = float(bracket.bracket_ceiling) if bracket.bracket_ceiling else float("inf")
        rate = float(bracket.rate)
        width = ceiling - floor
        taxable_in_bracket = min(remaining, width)
        if taxable_in_bracket > 0:
            federal_tax += taxable_in_bracket * rate
            remaining -= taxable_in_bracket
            marginal_rate = rate
        if remaining <= 0:
            break

    fed_effective = (federal_tax / gross_income) if gross_income > 0 else 0

    state_rate = 0.0
    if state_code:
        rule = session.query(StateTaxRule).filter_by(state_code=state_code).first()
        if rule:
            state_rate = float(rule.top_marginal_rate)

    state_tax = taxable_income * state_rate
    total_tax = federal_tax + state_tax
    effective = (total_tax / gross_income) if gross_income > 0 else 0

    return TaxPosition(
        gross_income=gross_income,
        taxable_income=taxable_income,
        standard_deduction=std_deduction,
        federal_tax=federal_tax,
        federal_effective_rate=fed_effective,
        federal_marginal_rate=marginal_rate,
        state_tax=state_tax,
        state_rate=state_rate,
        combined_marginal_rate=marginal_rate + state_rate,
        total_tax=total_tax,
        effective_rate=effective,
    )


def find_tlh_candidates(session: Session) -> list[TLHCandidate]:
    holdings = session.query(Holding).all()

    recent_sells = set()
    thirty_days_ago = date.today() - timedelta(days=30)
    sell_txs = (
        session.query(Transaction)
        .filter(
            Transaction.date >= thirty_days_ago,
            Transaction.description.ilike("%sell%"),
        )
        .all()
    )
    for tx in sell_txs:
        for word in tx.description.upper().split():
            if len(word) >= 2 and word.isalpha():
                recent_sells.add(word)

    candidates = []
    for h in holdings:
        if not h.current_price:
            continue
        current_value = float(h.current_price) * float(h.shares)
        cost = float(h.cost_basis)
        if current_value < cost:
            in_wash = h.symbol.upper() in recent_sells
            candidates.append(TLHCandidate(
                symbol=h.symbol,
                cost_basis=cost,
                current_value=current_value,
                unrealized_loss=cost - current_value,
                in_wash_window=in_wash,
            ))
    return sorted(candidates, key=lambda c: -c.unrealized_loss)
