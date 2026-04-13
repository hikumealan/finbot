"""Financial analysis chains combining computed metrics with LLM interpretation."""
from __future__ import annotations

from sqlalchemy.orm import Session

from finbot.analysis.expenses import expenses_by_category
from finbot.analysis.income import total_income
from finbot.analysis.net_worth import compute_net_worth
from finbot.analysis.savings_rate import overall_savings_rate
from finbot.llm.client import chat, is_ollama_available
from finbot.models.user_profile import UserProfile
from finbot.security.sanitizer import sanitize_for_llm


def build_financial_snapshot(session: Session) -> str:
    """Build a standardized context block for all advisors."""
    nw = compute_net_worth(session)
    income = total_income(session)
    expenses = expenses_by_category(session)
    savings = overall_savings_rate(session)

    profile = session.query(UserProfile).first()
    profile_str = ""
    if profile:
        profile_str = (
            f"Age: {profile.age}, State: {profile.state_of_residence}, "
            f"Risk tolerance: {profile.risk_tolerance}/10, "
            f"Filing status: {profile.filing_status}, "
            f"Target retirement: {profile.retirement_target_age}"
        )

    top_expenses = sorted(expenses.items(), key=lambda x: -x[1])[:5]
    expense_lines = "\n".join(f"  - {cat}: ${amt:,.2f}" for cat, amt in top_expenses)

    snapshot = f"""--- FINANCIAL SNAPSHOT ---
Net Worth: ${nw.net_worth:,.2f} (Assets: ${nw.total_assets:,.2f}, Liabilities: ${nw.total_liabilities:,.2f})
Total Income: ${income:,.2f}
Savings Rate: {savings:.1f}%
Emergency Fund: {nw.emergency_fund_months:.1f} months of expenses
Top Expenses:
{expense_lines}
Profile: {profile_str}
---"""
    return sanitize_for_llm(snapshot)


def ask_advisor(session: Session, system_prompt: str, user_message: str) -> str:
    """Send a question to an advisor with the financial snapshot injected."""
    if not is_ollama_available():
        return (
            "Ollama is not running. Start it with `ollama serve` to enable AI features.\n"
            "All data pages still work without Ollama — only the chat advisors require it."
        )

    snapshot = build_financial_snapshot(session)
    messages = [
        {"role": "system", "content": system_prompt + "\n\n" + snapshot},
        {"role": "user", "content": user_message},
    ]

    try:
        return chat(messages)
    except Exception as e:
        return f"LLM error: {e}"
