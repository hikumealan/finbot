"""Generate PDF financial reports as markdown-to-text (lightweight, no WeasyPrint dependency)."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from finbot.analysis.expenses import expenses_by_category, total_expenses
from finbot.analysis.income import total_income
from finbot.analysis.net_worth import compute_net_worth
from finbot.analysis.savings_rate import overall_savings_rate


def generate_report_text(session: Session, period: str = "Summary") -> str:
    nw = compute_net_worth(session)
    income = total_income(session)
    expenses = total_expenses(session)
    savings = overall_savings_rate(session)
    cats = expenses_by_category(session)

    lines = [
        f"# FinBot Financial Report — {period}",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Net Worth",
        f"- Total Assets: ${nw.total_assets:,.2f}",
        f"- Total Liabilities: ${nw.total_liabilities:,.2f}",
        f"- **Net Worth: ${nw.net_worth:,.2f}**",
        "",
        "## Income & Expenses",
        f"- Total Income: ${income:,.2f}",
        f"- Total Expenses: ${expenses:,.2f}",
        f"- Savings Rate: {savings:.1f}%",
        "",
        "## Expense Breakdown",
    ]

    for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
        pct = (amt / expenses * 100) if expenses > 0 else 0
        lines.append(f"- {cat}: ${amt:,.2f} ({pct:.1f}%)")

    lines.extend([
        "",
        "## Emergency Fund",
        f"- Liquid Savings: ${nw.liquid_savings:,.2f}",
        f"- Monthly Expenses: ${nw.avg_monthly_expenses:,.2f}",
        f"- Coverage: {nw.emergency_fund_months:.1f} months" if nw.emergency_fund_months != float("inf") else "- Coverage: N/A (no expenses recorded)",
        "",
        "---",
        "*This report is for informational purposes only and does not constitute financial advice.*",
    ])

    return "\n".join(lines)
