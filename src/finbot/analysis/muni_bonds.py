"""Municipal bond analysis: TEY, state rules, credit quality."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from finbot.models.holding import Holding
from finbot.models.reference import StateTaxRule


@dataclass
class MuniBondAnalysis:
    symbol: str
    coupon_rate: float
    tey: float
    is_in_state: bool
    is_state_exempt: bool
    credit_rating: str | None
    is_amt_subject: bool


def taxable_equivalent_yield(coupon: float, combined_tax_rate: float) -> float:
    if combined_tax_rate >= 1.0:
        return float("inf")
    return coupon / (1 - combined_tax_rate)


def quick_tey(coupon: float, federal_rate: float, state_rate: float = 0, in_state: bool = True) -> float:
    if in_state:
        combined = federal_rate + state_rate
    else:
        combined = federal_rate
    return taxable_equivalent_yield(coupon, combined)


def analyze_muni_holdings(
    session: Session,
    federal_marginal: float,
    state_code: str | None = None,
) -> list[MuniBondAnalysis]:
    state_rate = 0.0
    state_rule = None
    if state_code:
        state_rule = session.query(StateTaxRule).filter_by(state_code=state_code).first()
        if state_rule:
            state_rate = float(state_rule.top_marginal_rate)

    holdings = session.query(Holding).filter_by(asset_class="muni_bond").all()
    results = []

    for h in holdings:
        detail = h.muni_detail
        if not detail or not detail.coupon_rate:
            continue

        coupon = float(detail.coupon_rate)
        is_in_state = detail.issuer_state == state_code if state_code and detail.issuer_state else False

        is_exempt = False
        if state_rule:
            if state_rule.exempts_all_munis:
                is_exempt = True
            elif state_rule.exempts_own_munis and is_in_state:
                is_exempt = True

        combined = federal_marginal + (state_rate if is_exempt else 0)
        tey = taxable_equivalent_yield(coupon, combined)

        results.append(MuniBondAnalysis(
            symbol=h.symbol,
            coupon_rate=coupon,
            tey=tey,
            is_in_state=is_in_state,
            is_state_exempt=is_exempt,
            credit_rating=detail.credit_rating,
            is_amt_subject=detail.is_amt_subject,
        ))

    return results
