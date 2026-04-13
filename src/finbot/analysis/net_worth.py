"""Net worth calculation and emergency fund monitoring."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from finbot.analysis.expenses import total_expenses
from finbot.models.account import Account
from finbot.models.debt import Debt
from finbot.models.holding import Holding
from finbot.models.snapshot import Snapshot
from finbot.models.transaction import Transaction

_LIQUID_TYPES = {"checking", "savings"}


@dataclass
class NetWorthSummary:
    total_assets: float
    total_liabilities: float
    net_worth: float
    liquid_savings: float
    avg_monthly_expenses: float
    emergency_fund_months: float


def _account_balance(session: Session, account_id: int) -> float:
    """Net transaction flow for one account (income positive, expenses negative)."""
    result = (
        session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.account_id == account_id,
            Transaction.tx_type != "transfer",
        )
        .scalar()
    )
    return float(result)


def compute_net_worth(session: Session) -> NetWorthSummary:
    accounts = session.query(Account).all()

    cash_total = 0.0
    liquid_total = 0.0
    for acct in accounts:
        bal = _account_balance(session, acct.id)
        cash_total += bal
        if acct.account_type in _LIQUID_TYPES:
            liquid_total += bal

    holding_value = float(
        session.query(func.coalesce(func.sum(Holding.current_price * Holding.shares), 0)).scalar()
    )

    total_assets = cash_total + holding_value

    total_liabilities = float(
        session.query(func.coalesce(func.sum(Debt.principal), 0)).scalar()
    )

    today = date.today()
    if today.month > 6:
        six_months_ago = date(today.year, today.month - 6, 1)
    else:
        six_months_ago = date(today.year - 1, today.month + 6, 1)
    total_exp_6mo = total_expenses(session, six_months_ago, today)
    months_span = max(1, (today.year - six_months_ago.year) * 12 + today.month - six_months_ago.month)
    avg_monthly = total_exp_6mo / months_span if months_span > 0 else 0.0

    if avg_monthly > 0:
        emergency_months = max(liquid_total, 0) / avg_monthly
    else:
        emergency_months = float("inf")

    return NetWorthSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=total_assets - total_liabilities,
        liquid_savings=max(liquid_total, 0),
        avg_monthly_expenses=avg_monthly,
        emergency_fund_months=emergency_months,
    )


def record_snapshot(session: Session) -> Snapshot:
    nw = compute_net_worth(session)
    snap = Snapshot(
        date=date.today(),
        total_assets=nw.total_assets,
        total_liabilities=nw.total_liabilities,
        net_worth=nw.net_worth,
    )
    session.add(snap)
    session.flush()
    return snap


def get_snapshots(session: Session) -> list[Snapshot]:
    return session.query(Snapshot).order_by(Snapshot.date).all()
