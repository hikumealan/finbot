"""Budget variance tracking."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from finbot.analysis.expenses import expenses_by_category
from finbot.models.budget import Budget


@dataclass
class BudgetVariance:
    category: str
    budget: float
    actual: float
    variance: float
    pct: float

    @property
    def is_over(self) -> bool:
        return self.actual > self.budget


def get_budget_variance(session: Session, month: str) -> list[BudgetVariance]:
    """Compute budget variance for a given month (YYYY-MM)."""
    year, mon = int(month[:4]), int(month[5:7])
    start = date(year, mon, 1)
    if mon == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, mon + 1, 1)

    budgets = session.query(Budget).filter(Budget.effective_month <= month).all()
    latest_by_cat: dict[str, Budget] = {}
    for b in budgets:
        if b.category not in latest_by_cat or b.effective_month > latest_by_cat[b.category].effective_month:
            latest_by_cat[b.category] = b

    actuals = expenses_by_category(session, start, end, end_exclusive=True)

    results = []
    all_cats = set(latest_by_cat.keys()) | set(actuals.keys())
    for cat in sorted(all_cats):
        budget_amt = float(latest_by_cat[cat].monthly_limit) if cat in latest_by_cat else 0
        actual_amt = actuals.get(cat, 0)
        variance = budget_amt - actual_amt
        pct = (actual_amt / budget_amt * 100) if budget_amt > 0 else 0
        results.append(BudgetVariance(
            category=cat,
            budget=budget_amt,
            actual=actual_amt,
            variance=variance,
            pct=pct,
        ))

    return results


def set_budget(session: Session, category: str, amount: float, month: str) -> Budget:
    existing = session.query(Budget).filter_by(category=category, effective_month=month).first()
    if existing:
        existing.monthly_limit = amount
        session.flush()
        return existing
    b = Budget(category=category, monthly_limit=amount, effective_month=month)
    session.add(b)
    session.flush()
    return b
