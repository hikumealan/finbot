"""Growth projections with Monte Carlo simulation."""
from __future__ import annotations

import random
from dataclasses import dataclass

from finbot.config import settings


@dataclass
class ProjectionResult:
    years: int
    nominal: list[float]  # year-by-year balances
    real: list[float]  # inflation-adjusted
    percentiles: dict[int, float]  # Monte Carlo percentile outcomes


def compound_growth(
    initial: float,
    annual_contribution: float,
    rate: float,
    years: int,
    inflation: float | None = None,
) -> tuple[list[float], list[float]]:
    inflation = inflation or settings.default_inflation_rate
    nominal = []
    real = []
    balance = initial

    for y in range(1, years + 1):
        balance = balance * (1 + rate) + annual_contribution
        nominal.append(balance)
        real_balance = balance / ((1 + inflation) ** y)
        real.append(real_balance)

    return nominal, real


def monte_carlo(
    initial: float,
    annual_contribution: float,
    years: int,
    mean_return: float = 0.07,
    std_dev: float = 0.15,
    simulations: int = 1000,
    inflation: float | None = None,
) -> ProjectionResult:
    inflation = inflation or settings.default_inflation_rate

    final_values = []
    for _ in range(simulations):
        balance = initial
        for y in range(years):
            annual_return = random.gauss(mean_return, std_dev)
            balance = balance * (1 + annual_return) + annual_contribution
            balance = max(0, balance)
        final_values.append(balance)

    final_values.sort()

    percentile_keys = [5, 25, 50, 75, 95]
    percentiles = {}
    for p in percentile_keys:
        idx = int(len(final_values) * p / 100)
        percentiles[p] = final_values[min(idx, len(final_values) - 1)]

    nominal, real = compound_growth(initial, annual_contribution, mean_return, years, inflation)

    return ProjectionResult(
        years=years,
        nominal=nominal,
        real=real,
        percentiles=percentiles,
    )
