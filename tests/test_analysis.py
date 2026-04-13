"""Tests for core financial analysis modules."""
from datetime import date

import pytest

from finbot.analysis.debts import amortization_months
from finbot.analysis.expenses import expenses_by_category, total_expenses
from finbot.analysis.investments import fee_impact
from finbot.analysis.muni_bonds import quick_tey, taxable_equivalent_yield
from finbot.analysis.projections import compound_growth
from finbot.db.database import get_session, init_db
from finbot.db.seed import seed_all
from finbot.models.account import Account
from finbot.models.transaction import Transaction
from finbot.security.sanitizer import sanitize_for_llm


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Create a fresh in-memory-like DB for each test."""
    from finbot.config import settings

    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    monkeypatch.setattr(settings, "key_dir", tmp_path / "keys")
    settings.ensure_dirs()
    init_db()
    with get_session() as session:
        seed_all(session)
    yield


class TestAmortization:
    def test_zero_rate(self):
        months, interest = amortization_months(1000, 0, 500)
        assert months == 2
        assert interest == 0

    def test_zero_rate_exact_multiple(self):
        months, interest = amortization_months(100, 0, 50)
        assert months == 2
        assert interest == 0

    def test_normal_rate(self):
        months, interest = amortization_months(10000, 0.05, 200)
        assert 50 < months < 80
        assert interest > 0

    def test_payment_less_than_interest(self):
        months, interest = amortization_months(100000, 0.20, 100)
        assert months == 600


class TestFeeImpact:
    def test_fee_drag_positive(self):
        result = fee_impact(100000, 0.0085, 30)
        assert result["fee_drag"] > 100000
        assert result["high_cost_final"] < result["low_cost_final"]

    def test_zero_er(self):
        result = fee_impact(100000, 0, 30, 0)
        assert abs(result["fee_drag"]) < 1


class TestTEY:
    def test_basic_tey(self):
        tey = taxable_equivalent_yield(0.035, 0.35)
        assert abs(tey - 0.05385) < 0.001

    def test_quick_tey_in_state(self):
        tey = quick_tey(0.035, 0.32, 0.05, in_state=True)
        assert tey > 0.035

    def test_rate_at_100_pct(self):
        tey = taxable_equivalent_yield(0.035, 1.0)
        assert tey == float("inf")


class TestCompoundGrowth:
    def test_nominal_grows(self):
        nominal, real = compound_growth(100000, 12000, 0.07, 30)
        assert len(nominal) == 30
        assert nominal[-1] > 100000
        assert real[-1] < nominal[-1]

    def test_real_less_than_nominal(self):
        nominal, real = compound_growth(100000, 0, 0.07, 10, inflation=0.03)
        for n, r in zip(nominal, real):
            assert r < n


class TestSanitizer:
    def test_ssn_stripped(self):
        result = sanitize_for_llm("SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "SSN_REDACTED" in result

    def test_email_stripped(self):
        result = sanitize_for_llm("email: test@example.com")
        assert "test@example.com" not in result

    def test_custom_replacements(self):
        result = sanitize_for_llm("John Doe owes $500", {"John Doe": "[NAME_1]"})
        assert "John Doe" not in result
        assert "[NAME_1]" in result


class TestExpenses:
    def test_empty_db(self):
        with get_session() as session:
            total = total_expenses(session)
            assert total == 0

    def test_with_transactions(self):
        with get_session() as session:
            acct = Account(institution="Test", name="Checking", account_type="checking")
            session.add(acct)
            session.flush()
            session.add(Transaction(
                account_id=acct.id, date=date(2025, 3, 1),
                amount=-50.0, description="Groceries", tx_type="expense",
            ))
            session.add(Transaction(
                account_id=acct.id, date=date(2025, 3, 2),
                amount=-30.0, description="Gas", tx_type="expense",
            ))
            session.commit()

            total = total_expenses(session)
            assert total == 80.0

            cats = expenses_by_category(session)
            assert len(cats) == 1  # both uncategorized
