"""Investment performance analysis."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from finbot.models.holding import Holding


@dataclass
class PortfolioSummary:
    total_value: float
    total_cost_basis: float
    total_gain_loss: float
    total_return_pct: float
    allocation: dict[str, float]  # asset_class -> percentage


def portfolio_summary(session: Session) -> PortfolioSummary:
    holdings = session.query(Holding).all()

    total_value = 0.0
    total_cost = 0.0
    alloc: dict[str, float] = {}

    for h in holdings:
        price = float(h.current_price or 0)
        shares = float(h.shares)
        value = price * shares
        total_value += value
        total_cost += float(h.cost_basis)
        alloc[h.asset_class] = alloc.get(h.asset_class, 0) + value

    if total_value > 0:
        alloc = {k: v / total_value * 100 for k, v in alloc.items()}

    gain = total_value - total_cost
    ret_pct = (gain / total_cost * 100) if total_cost > 0 else 0

    return PortfolioSummary(
        total_value=total_value,
        total_cost_basis=total_cost,
        total_gain_loss=gain,
        total_return_pct=ret_pct,
        allocation=alloc,
    )


def fee_impact(balance: float, expense_ratio: float, years: int = 30, alternative_er: float = 0.0003) -> dict[str, float]:
    """Project the cumulative cost of an expense ratio vs a low-cost alternative."""
    growth_rate = 0.07

    def _project(er: float) -> float:
        val = balance
        for _ in range(years):
            val *= (1 + growth_rate - er)
        return val

    high_cost = _project(expense_ratio)
    low_cost = _project(alternative_er)

    return {
        "high_cost_final": high_cost,
        "low_cost_final": low_cost,
        "fee_drag": low_cost - high_cost,
        "years": years,
    }
