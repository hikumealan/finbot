"""Debt payoff modeling: amortization, avalanche, and snowball strategies."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from finbot.models.debt import Debt


@dataclass
class PayoffResult:
    name: str
    months_to_payoff: int
    total_interest: float
    total_paid: float


@dataclass
class PayoffComparison:
    avalanche: list[PayoffResult]
    snowball: list[PayoffResult]
    avalanche_total_interest: float
    snowball_total_interest: float
    interest_saved: float


def amortization_months(principal: float, rate: float, payment: float) -> tuple[int, float]:
    """Return (months_to_payoff, total_interest) for a fixed payment schedule."""
    if rate == 0:
        if payment <= 0:
            return 0, 0.0
        months = -(-int(principal) // int(payment)) if payment > 0 else 0
        return max(months, 0), 0.0

    monthly_rate = rate / 12
    balance = principal
    total_interest = 0.0
    months = 0
    max_months = 600

    while balance > 0.01 and months < max_months:
        interest = balance * monthly_rate
        total_interest += interest
        principal_payment = min(payment - interest, balance)
        if principal_payment <= 0:
            return max_months, total_interest
        balance -= principal_payment
        months += 1

    return months, total_interest


def _simulate_strategy(debts_data: list[dict], extra_payment: float) -> list[PayoffResult]:
    """Simulate multi-debt payoff with simultaneous minimum payments.

    All debts receive minimum payments each month. The extra payment
    (plus any freed minimums from paid-off debts) goes to the first
    debt in the list (the priority target).
    """
    active = []
    for d in debts_data:
        active.append({
            "name": d["name"],
            "balance": d["principal"],
            "rate": d["rate"],
            "min_payment": d["min_payment"],
            "months": 0,
            "total_interest": 0.0,
        })

    results = []
    max_months = 600

    for month_tick in range(1, max_months + 1):
        if not active:
            break

        freed_from_payoffs = 0.0

        for debt in active:
            monthly_rate = debt["rate"] / 12
            interest = debt["balance"] * monthly_rate
            debt["total_interest"] += interest
            debt["balance"] += interest

        available_extra = extra_payment + freed_from_payoffs
        for i, debt in enumerate(active):
            if i == 0:
                payment = debt["min_payment"] + available_extra
            else:
                payment = debt["min_payment"]

            actual = min(payment, debt["balance"])
            debt["balance"] -= actual
            debt["months"] = month_tick

        newly_paid = []
        for debt in active:
            if debt["balance"] <= 0.01:
                results.append(PayoffResult(
                    name=debt["name"],
                    months_to_payoff=debt["months"],
                    total_interest=debt["total_interest"],
                    total_paid=0.0,
                ))
                freed_from_payoffs += debt["min_payment"]
                extra_payment += debt["min_payment"]
                newly_paid.append(debt)

        for debt in newly_paid:
            active.remove(debt)

    for debt in active:
        results.append(PayoffResult(
            name=debt["name"],
            months_to_payoff=max_months,
            total_interest=debt["total_interest"],
            total_paid=0.0,
        ))

    for r in results:
        r.total_paid = r.total_interest + next(
            (d["principal"] for d in debts_data if d["name"] == r.name), 0
        )

    return results


def compare_strategies(session: Session, extra_payment: float = 0) -> PayoffComparison:
    debts = session.query(Debt).all()
    if not debts:
        return PayoffComparison([], [], 0, 0, 0)

    debts_data = [
        {
            "name": d.name,
            "principal": float(d.principal),
            "rate": float(d.interest_rate),
            "min_payment": float(d.minimum_payment),
        }
        for d in debts
    ]

    avalanche_order = sorted(debts_data, key=lambda d: -d["rate"])
    snowball_order = sorted(debts_data, key=lambda d: d["principal"])

    aval = _simulate_strategy([dict(d) for d in avalanche_order], extra_payment)
    snow = _simulate_strategy([dict(d) for d in snowball_order], extra_payment)

    aval_interest = sum(r.total_interest for r in aval)
    snow_interest = sum(r.total_interest for r in snow)

    return PayoffComparison(
        avalanche=aval,
        snowball=snow,
        avalanche_total_interest=aval_interest,
        snowball_total_interest=snow_interest,
        interest_saved=snow_interest - aval_interest,
    )
