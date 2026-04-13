"""Seed reference data for state tax rules and federal tax brackets."""
from __future__ import annotations

from sqlalchemy.orm import Session

from finbot.models.reference import FederalTaxBracket, StateTaxRule

# fmt: off
_STATE_TAX_DATA: list[tuple[str, bool, bool, bool, float, str | None]] = [
    ("AL", True,  True,  False, 0.0500, None),
    ("AK", False, False, False, 0.0000, "No state income tax"),
    ("AZ", True,  True,  False, 0.0259, None),
    ("AR", True,  True,  False, 0.0439, None),
    ("CA", True,  True,  False, 0.1330, None),
    ("CO", True,  True,  False, 0.0440, None),
    ("CT", True,  True,  False, 0.0699, None),
    ("DE", True,  True,  False, 0.0660, None),
    ("FL", False, False, False, 0.0000, "No state income tax"),
    ("GA", True,  True,  False, 0.0549, None),
    ("HI", True,  True,  False, 0.1100, None),
    ("ID", True,  True,  False, 0.0580, None),
    ("IL", True,  False, True,  0.0495, "Exempts all munis"),
    ("IN", True,  True,  False, 0.0305, None),
    ("IA", True,  True,  False, 0.0570, None),
    ("KS", True,  True,  False, 0.0570, None),
    ("KY", True,  True,  False, 0.0400, None),
    ("LA", True,  True,  False, 0.0425, None),
    ("ME", True,  True,  False, 0.0715, None),
    ("MD", True,  True,  False, 0.0575, None),
    ("MA", True,  True,  False, 0.0500, None),
    ("MI", True,  True,  False, 0.0425, None),
    ("MN", True,  True,  False, 0.0985, None),
    ("MS", True,  True,  False, 0.0500, None),
    ("MO", True,  True,  False, 0.0495, None),
    ("MT", True,  True,  False, 0.0675, None),
    ("NE", True,  True,  False, 0.0664, None),
    ("NV", False, False, False, 0.0000, "No state income tax"),
    ("NH", False, False, False, 0.0000, "No tax on earned income"),
    ("NJ", True,  True,  False, 0.1075, None),
    ("NM", True,  True,  False, 0.0590, None),
    ("NY", True,  True,  False, 0.1090, None),
    ("NC", True,  True,  False, 0.0450, None),
    ("ND", True,  True,  False, 0.0250, None),
    ("OH", True,  True,  False, 0.0399, None),
    ("OK", True,  True,  False, 0.0475, None),
    ("OR", True,  True,  False, 0.0990, None),
    ("PA", True,  True,  False, 0.0307, None),
    ("RI", True,  True,  False, 0.0599, None),
    ("SC", True,  True,  False, 0.0700, None),
    ("SD", False, False, False, 0.0000, "No state income tax"),
    ("TN", False, False, False, 0.0000, "No state income tax"),
    ("TX", False, False, False, 0.0000, "No state income tax"),
    ("UT", True,  True,  False, 0.0465, None),
    ("VT", True,  True,  False, 0.0875, None),
    ("VA", True,  True,  False, 0.0575, None),
    ("WA", False, False, False, 0.0000, "No state income tax"),
    ("WV", True,  True,  False, 0.0650, None),
    ("WI", True,  True,  False, 0.0753, None),
    ("WY", False, False, False, 0.0000, "No state income tax"),
    ("DC", True,  True,  False, 0.1075, None),
]
# fmt: on

_FEDERAL_BRACKETS_2025: list[tuple[str, float, float | None, float]] = [
    # (filing_status, floor, ceiling, rate)
    ("single", 0, 11925, 0.10),
    ("single", 11925, 48475, 0.12),
    ("single", 48475, 103350, 0.22),
    ("single", 103350, 197300, 0.24),
    ("single", 197300, 250525, 0.32),
    ("single", 250525, 626350, 0.35),
    ("single", 626350, None, 0.37),
    ("married_joint", 0, 23850, 0.10),
    ("married_joint", 23850, 96950, 0.12),
    ("married_joint", 96950, 206700, 0.22),
    ("married_joint", 206700, 394600, 0.24),
    ("married_joint", 394600, 501050, 0.32),
    ("married_joint", 501050, 751600, 0.35),
    ("married_joint", 751600, None, 0.37),
    ("married_separate", 0, 11925, 0.10),
    ("married_separate", 11925, 48475, 0.12),
    ("married_separate", 48475, 103350, 0.22),
    ("married_separate", 103350, 197300, 0.24),
    ("married_separate", 197300, 250525, 0.32),
    ("married_separate", 250525, 375800, 0.35),
    ("married_separate", 375800, None, 0.37),
    ("head_of_household", 0, 17000, 0.10),
    ("head_of_household", 17000, 64850, 0.12),
    ("head_of_household", 64850, 103350, 0.22),
    ("head_of_household", 103350, 197300, 0.24),
    ("head_of_household", 197300, 250500, 0.32),
    ("head_of_household", 250500, 626350, 0.35),
    ("head_of_household", 626350, None, 0.37),
]


def seed_state_tax_rules(session: Session) -> int:
    existing = session.query(StateTaxRule).count()
    if existing > 0:
        return 0

    count = 0
    for code, has_tax, own_munis, all_munis, rate, notes in _STATE_TAX_DATA:
        session.add(StateTaxRule(
            state_code=code,
            has_income_tax=has_tax,
            exempts_own_munis=own_munis,
            exempts_all_munis=all_munis,
            top_marginal_rate=rate,
            notes=notes,
        ))
        count += 1
    session.flush()
    return count


def seed_federal_brackets(session: Session, tax_year: int = 2025) -> int:
    if tax_year != 2025:
        raise ValueError(
            f"Bracket data is only available for 2025. "
            f"Got tax_year={tax_year}. Update _FEDERAL_BRACKETS_2025 for other years."
        )

    existing = session.query(FederalTaxBracket).filter_by(tax_year=tax_year).count()
    if existing > 0:
        return 0

    count = 0
    for status, floor, ceiling, rate in _FEDERAL_BRACKETS_2025:
        session.add(FederalTaxBracket(
            tax_year=tax_year,
            filing_status=status,
            bracket_floor=floor,
            bracket_ceiling=ceiling,
            rate=rate,
        ))
        count += 1
    session.flush()
    return count


def seed_all(session: Session) -> dict[str, int]:
    results = {
        "state_tax_rules": seed_state_tax_rules(session),
        "federal_tax_brackets": seed_federal_brackets(session),
    }
    session.commit()
    return results
