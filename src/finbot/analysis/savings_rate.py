"""Savings rate calculation: (Income - Expenses) / Income."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from finbot.analysis.expenses import expenses_by_month
from finbot.analysis.income import income_by_month


@dataclass
class SavingsRateResult:
    month: str
    income: float
    expenses: float
    savings: float
    rate: float  # percentage


def monthly_savings_rates(session: Session) -> list[SavingsRateResult]:
    inc = income_by_month(session)
    exp = expenses_by_month(session)

    months = sorted(set(inc.keys()) | set(exp.keys()))
    results = []
    for month in months:
        income = inc.get(month, 0)
        expenses = exp.get(month, 0)
        savings = income - expenses
        rate = (savings / income * 100) if income > 0 else 0
        results.append(SavingsRateResult(
            month=month, income=income, expenses=expenses, savings=savings, rate=rate,
        ))
    return results


def overall_savings_rate(session: Session) -> float:
    rates = monthly_savings_rates(session)
    if not rates:
        return 0
    total_income = sum(r.income for r in rates)
    total_expenses = sum(r.expenses for r in rates)
    if total_income == 0:
        return 0
    return (total_income - total_expenses) / total_income * 100
