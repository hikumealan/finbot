"""Financial goal progress tracking."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from finbot.models.goal import Goal


@dataclass
class GoalProgress:
    name: str
    goal_type: str
    target: float
    current: float
    progress_pct: float
    monthly_needed: float
    status: str  # on_track / behind / ahead / complete


def compute_goal_progress(session: Session) -> list[GoalProgress]:
    goals = session.query(Goal).all()
    today = date.today()
    results = []

    for g in goals:
        current = float(g.current_amount)
        target = float(g.target_amount)
        pct = (current / target * 100) if target > 0 else 0

        if g.target_date and g.target_date > today:
            months_left = max(1, (g.target_date.year - today.year) * 12 + g.target_date.month - today.month)
            remaining = max(0, target - current)
            monthly_needed = remaining / months_left

            total_months = max(1, (g.target_date.year - today.year) * 12 + g.target_date.month - today.month + int(months_left))
            elapsed_fraction = 1 - (months_left / (months_left + max(1, total_months - months_left)))
            expected_pct = elapsed_fraction * 100

            if pct >= 100:
                status = "complete"
            elif pct > expected_pct * 1.1:
                status = "ahead"
            elif pct >= expected_pct * 0.9:
                status = "on_track"
            else:
                status = "behind"
        else:
            monthly_needed = 0.0
            status = "complete" if pct >= 100 else "on_track"

        results.append(GoalProgress(
            name=g.name,
            goal_type=g.goal_type,
            target=target,
            current=current,
            progress_pct=min(pct, 100),
            monthly_needed=monthly_needed,
            status=status,
        ))

    return results
