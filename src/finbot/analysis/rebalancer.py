"""Portfolio rebalancing engine."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from finbot.analysis.investments import portfolio_summary
from finbot.config import settings


@dataclass
class RebalanceSuggestion:
    asset_class: str
    current_pct: float
    target_pct: float
    drift: float
    action: str  # "buy" or "sell"
    amount: float  # dollar amount to trade


_DEFAULT_TARGETS = {
    "equity": 60.0,
    "bond": 25.0,
    "muni_bond": 5.0,
    "reit": 5.0,
    "cash": 5.0,
}


def check_rebalance(
    session: Session,
    targets: dict[str, float] | None = None,
    threshold: float | None = None,
) -> list[RebalanceSuggestion]:
    targets = targets or _DEFAULT_TARGETS
    threshold = threshold or settings.rebalance_drift_threshold * 100

    summary = portfolio_summary(session)
    if summary.total_value == 0:
        return []

    suggestions = []
    all_classes = set(targets.keys()) | set(summary.allocation.keys())

    for ac in sorted(all_classes):
        current = summary.allocation.get(ac, 0)
        target = targets.get(ac, 0)
        drift = current - target

        if abs(drift) >= threshold:
            action = "sell" if drift > 0 else "buy"
            amount = abs(drift / 100 * summary.total_value)
            suggestions.append(RebalanceSuggestion(
                asset_class=ac,
                current_pct=current,
                target_pct=target,
                drift=drift,
                action=action,
                amount=amount,
            ))

    return suggestions
