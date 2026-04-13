"""Pydantic request/response schemas for the API."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


# ── Dashboard ─────────────────────────────────────────────────────
class DashboardSummary(BaseModel):
    net_worth: float
    total_assets: float
    total_liabilities: float
    liquid_savings: float
    emergency_fund_months: float
    total_income: float
    total_expenses: float
    savings_rate: float
    expenses_by_category: dict[str, float]
    expenses_by_month: dict[str, float]


# ── Transactions ──────────────────────────────────────────────────
class TransactionOut(BaseModel):
    id: int
    account_id: int
    date: date
    amount: float
    description: str
    category: str | None
    subcategory: str | None
    tx_type: str
    source_file: str | None
    is_recurring: bool

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    description: str | None = None
    amount: float | None = None
    tx_type: str | None = None


# ── Accounts ──────────────────────────────────────────────────────
class AccountOut(BaseModel):
    id: int
    institution: str
    name: str
    account_type: str
    currency: str
    is_tax_advantaged: bool
    transaction_count: int = 0
    last_activity: str | None = None

    model_config = {"from_attributes": True}


class AccountCreate(BaseModel):
    institution: str
    name: str
    account_type: str = "checking"
    is_tax_advantaged: bool = False


class AccountUpdate(BaseModel):
    name: str | None = None
    institution: str | None = None
    account_type: str | None = None


class MergeRequest(BaseModel):
    source_id: int
    target_id: int


# ── Goals ─────────────────────────────────────────────────────────
class GoalOut(BaseModel):
    id: int
    name: str
    goal_type: str
    target_amount: float
    current_amount: float
    target_date: date | None
    progress_pct: float = 0
    monthly_needed: float = 0
    status: str = "on_track"

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    name: str
    goal_type: str
    target_amount: float
    current_amount: float = 0
    target_date: date | None = None


# ── Debts ─────────────────────────────────────────────────────────
class DebtOut(BaseModel):
    id: int
    name: str
    principal: float
    interest_rate: float
    minimum_payment: float
    term_months: int | None
    debt_type: str

    model_config = {"from_attributes": True}


class DebtCreate(BaseModel):
    name: str
    principal: float
    interest_rate: float
    minimum_payment: float
    term_months: int | None = None
    debt_type: str = "credit_card"


# ── Budget ────────────────────────────────────────────────────────
class BudgetOut(BaseModel):
    category: str
    monthly_limit: float
    effective_month: str


class BudgetSet(BaseModel):
    category: str
    monthly_limit: float
    month: str | None = None


class BudgetVarianceOut(BaseModel):
    category: str
    budget: float
    actual: float
    variance: float
    pct: float
    is_over: bool


# ── Chat ──────────────────────────────────────────────────────────
class ChatSessionOut(BaseModel):
    id: int
    advisor_type: str
    title: str | None
    created_at: str
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
    advisor_type: str = "boglehead"
    session_id: int | None = None


# ── Tax ───────────────────────────────────────────────────────────
class TaxPositionOut(BaseModel):
    gross_income: float
    taxable_income: float
    standard_deduction: float
    federal_tax: float
    federal_effective_rate: float
    federal_marginal_rate: float
    state_tax: float
    state_rate: float
    combined_marginal_rate: float
    total_tax: float
    effective_rate: float


class TLHCandidateOut(BaseModel):
    symbol: str
    cost_basis: float
    current_value: float
    unrealized_loss: float
    in_wash_window: bool


# ── Investments ───────────────────────────────────────────────────
class PortfolioSummaryOut(BaseModel):
    total_value: float
    total_cost_basis: float
    total_gain_loss: float
    total_return_pct: float
    allocation: dict[str, float]


class FeeImpactRequest(BaseModel):
    balance: float
    expense_ratio: float
    years: int = 30


class FeeImpactOut(BaseModel):
    high_cost_final: float
    low_cost_final: float
    fee_drag: float
    years: int


# ── Projections ───────────────────────────────────────────────────
class MonteCarloRequest(BaseModel):
    initial: float
    annual_contribution: float = 12000
    years: int = 30
    inflation: float = 0.03


class MonteCarloOut(BaseModel):
    years: int
    nominal: list[float]
    real: list[float]
    percentiles: dict[int, float]


# ── Config ────────────────────────────────────────────────────────
class ConfigUpdate(BaseModel):
    section: str
    key: str
    value: str | float | int | bool


# ── Settings ──────────────────────────────────────────────────────
class ProfileOut(BaseModel):
    age: int | None
    state_of_residence: str | None
    risk_tolerance: int
    retirement_target_age: int | None
    filing_status: str | None
    employer_match_pct: float | None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    age: int | None = None
    state_of_residence: str | None = None
    risk_tolerance: int | None = None
    retirement_target_age: int | None = None
    filing_status: str | None = None
    employer_match_pct: float | None = None


class ClearRequest(BaseModel):
    targets: list[str]


class PinRequest(BaseModel):
    pin: str
    current_pin: str | None = None


class DbStats(BaseModel):
    accounts: int
    transactions: int
    holdings: int
    tax_documents: int
    chat_sessions: int
    audit_entries: int
    budgets: int
    goals: int
    debts: int
    snapshots: int
    prompts: int
    category_rules: int


# ── Guide ─────────────────────────────────────────────────────────
class GuideSection(BaseModel):
    title: str
    content: str


class SearchResult(BaseModel):
    title: str
    snippet: str
