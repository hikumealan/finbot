"""Paycheck analyzer and what-if planner."""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from finbot.models.reference import FederalTaxBracket, StateTaxRule

SS_RATE = 0.062
SS_WAGE_BASE = 168600
MEDICARE_RATE = 0.0145
MEDICARE_ADDITIONAL_RATE = 0.009
MEDICARE_ADDITIONAL_THRESHOLD = 200000

_PAY_PERIODS = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}

STANDARD_DEDUCTION_2025 = {
    "single": 15000,
    "married_joint": 30000,
    "married_separate": 15000,
    "head_of_household": 22500,
}

HSA_LIMIT_2025 = {"single": 4300, "family": 8550}
K401_LIMIT_2025 = 23500


@dataclass
class PaycheckLine:
    label: str
    annual: float
    per_period: float
    pct_of_gross: float = 0.0


@dataclass
class PaycheckBreakdown:
    gross: PaycheckLine
    federal_tax: PaycheckLine
    state_tax: PaycheckLine
    social_security: PaycheckLine
    medicare: PaycheckLine
    k401_contribution: PaycheckLine
    hsa_contribution: PaycheckLine
    insurance: PaycheckLine
    net_pay: PaycheckLine
    all_lines: list[PaycheckLine] = field(default_factory=list)
    effective_tax_rate: float = 0.0


def _compute_federal_tax(taxable_income: float, filing_status: str, session: Session | None = None) -> float:
    if session:
        brackets = (
            session.query(FederalTaxBracket)
            .filter_by(tax_year=2025, filing_status=filing_status)
            .order_by(FederalTaxBracket.bracket_floor)
            .all()
        )
    else:
        brackets = []

    if not brackets:
        brackets_data = _DEFAULT_BRACKETS.get(filing_status, _DEFAULT_BRACKETS["single"])
        tax = 0.0
        remaining = taxable_income
        for floor, ceiling, rate in brackets_data:
            width = (ceiling or float("inf")) - floor
            taxable_in_bracket = min(remaining, width)
            if taxable_in_bracket > 0:
                tax += taxable_in_bracket * rate
                remaining -= taxable_in_bracket
            if remaining <= 0:
                break
        return tax

    tax = 0.0
    remaining = taxable_income
    for b in brackets:
        floor = float(b.bracket_floor)
        ceiling = float(b.bracket_ceiling) if b.bracket_ceiling else float("inf")
        rate = float(b.rate)
        width = ceiling - floor
        taxable_in_bracket = min(remaining, width)
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * rate
            remaining -= taxable_in_bracket
        if remaining <= 0:
            break
    return tax


_DEFAULT_BRACKETS = {
    "single": [
        (0, 11925, 0.10), (11925, 48475, 0.12), (48475, 103350, 0.22),
        (103350, 197300, 0.24), (197300, 250525, 0.32), (250525, 626350, 0.35), (626350, None, 0.37),
    ],
    "married_joint": [
        (0, 23850, 0.10), (23850, 96950, 0.12), (96950, 206700, 0.22),
        (206700, 394600, 0.24), (394600, 501050, 0.32), (501050, 751600, 0.35), (751600, None, 0.37),
    ],
}


def _compute_state_tax(taxable_income: float, state: str | None, session: Session | None = None) -> float:
    if not state:
        return 0.0
    if session:
        rule = session.query(StateTaxRule).filter_by(state_code=state).first()
        if rule:
            return taxable_income * float(rule.top_marginal_rate)
    return 0.0


def analyze_paycheck(
    gross_salary: float,
    pay_frequency: str = "biweekly",
    filing_status: str = "single",
    state: str | None = None,
    k401_pct: float = 0.0,
    hsa_annual: float = 0.0,
    insurance_annual: float = 0.0,
    session: Session | None = None,
) -> PaycheckBreakdown:
    """Full paycheck breakdown."""
    periods = _PAY_PERIODS.get(pay_frequency, 26)

    # Pre-tax deductions
    k401_annual = min(gross_salary * k401_pct / 100, K401_LIMIT_2025)
    hsa_annual_actual = min(hsa_annual, HSA_LIMIT_2025.get("family", 8550))
    total_pretax = k401_annual + hsa_annual_actual + insurance_annual

    # Taxable income
    std_deduction = STANDARD_DEDUCTION_2025.get(filing_status, 15000)
    taxable_income = max(0, gross_salary - total_pretax - std_deduction)

    # Taxes
    federal = _compute_federal_tax(taxable_income, filing_status, session)
    state_tax = _compute_state_tax(max(0, gross_salary - total_pretax - std_deduction), state, session)

    ss_taxable = min(gross_salary, SS_WAGE_BASE)
    ss_tax = ss_taxable * SS_RATE
    medicare_tax = gross_salary * MEDICARE_RATE
    if gross_salary > MEDICARE_ADDITIONAL_THRESHOLD:
        medicare_tax += (gross_salary - MEDICARE_ADDITIONAL_THRESHOLD) * MEDICARE_ADDITIONAL_RATE

    net = gross_salary - federal - state_tax - ss_tax - medicare_tax - total_pretax

    def _line(label: str, annual: float) -> PaycheckLine:
        return PaycheckLine(label=label, annual=round(annual, 2), per_period=round(annual / periods, 2), pct_of_gross=round(annual / gross_salary * 100, 1) if gross_salary > 0 else 0)

    lines = [
        gross_line := _line("Gross Pay", gross_salary),
        fed_line := _line("Federal Income Tax", -federal),
        state_line := _line("State Income Tax", -state_tax),
        ss_line := _line("Social Security", -ss_tax),
        med_line := _line("Medicare", -medicare_tax),
        k401_line := _line("401(k) Contribution", -k401_annual),
        hsa_line := _line("HSA Contribution", -hsa_annual_actual),
        ins_line := _line("Insurance Premiums", -insurance_annual),
        net_line := _line("Net Pay", net),
    ]

    total_tax = federal + state_tax + ss_tax + medicare_tax
    effective_rate = (total_tax / gross_salary * 100) if gross_salary > 0 else 0

    return PaycheckBreakdown(
        gross=gross_line, federal_tax=fed_line, state_tax=state_line,
        social_security=ss_line, medicare=med_line, k401_contribution=k401_line,
        hsa_contribution=hsa_line, insurance=ins_line, net_pay=net_line,
        all_lines=lines, effective_tax_rate=round(effective_rate, 1),
    )


def compare_paychecks(
    current: dict,
    proposed: dict,
    session: Session | None = None,
) -> dict:
    """Compare current vs proposed paycheck configuration."""
    current_breakdown = analyze_paycheck(**current, session=session)
    proposed_breakdown = analyze_paycheck(**proposed, session=session)

    comparison = []
    for curr_line, prop_line in zip(current_breakdown.all_lines, proposed_breakdown.all_lines):
        delta = prop_line.annual - curr_line.annual
        comparison.append({
            "label": curr_line.label,
            "current_annual": curr_line.annual,
            "current_per_period": curr_line.per_period,
            "proposed_annual": prop_line.annual,
            "proposed_per_period": prop_line.per_period,
            "delta_annual": round(delta, 2),
            "delta_per_period": round(delta / (_PAY_PERIODS.get(proposed.get("pay_frequency", "biweekly"), 26)), 2),
        })

    return {
        "comparison": comparison,
        "current_effective_rate": current_breakdown.effective_tax_rate,
        "proposed_effective_rate": proposed_breakdown.effective_tax_rate,
        "net_pay_change_annual": round(proposed_breakdown.net_pay.annual - current_breakdown.net_pay.annual, 2),
    }
