export interface DashboardSummary {
  net_worth: number;
  total_assets: number;
  total_liabilities: number;
  liquid_savings: number;
  emergency_fund_months: number;
  total_income: number;
  total_expenses: number;
  savings_rate: number;
  expenses_by_category: Record<string, number>;
  expenses_by_month: Record<string, number>;
}

export interface Transaction {
  id: number;
  account_id: number;
  date: string;
  amount: number;
  description: string;
  category: string | null;
  subcategory: string | null;
  tx_type: string;
  source_file: string | null;
  is_recurring: boolean;
}

export interface Account {
  id: number;
  institution: string;
  name: string;
  account_type: string;
  currency: string;
  is_tax_advantaged: boolean;
  transaction_count: number;
  last_activity: string | null;
}

export interface Goal {
  id: number;
  name: string;
  goal_type: string;
  target_amount: number;
  current_amount: number;
  target_date: string | null;
  progress_pct: number;
  monthly_needed: number;
  status: string;
}

export interface Debt {
  id: number;
  name: string;
  principal: number;
  interest_rate: number;
  minimum_payment: number;
  term_months: number | null;
  debt_type: string;
}

export interface ChatSession {
  id: number;
  advisor_type: string;
  title: string | null;
  created_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface TaxPosition {
  gross_income: number;
  taxable_income: number;
  standard_deduction: number;
  federal_tax: number;
  federal_effective_rate: number;
  federal_marginal_rate: number;
  state_tax: number;
  state_rate: number;
  combined_marginal_rate: number;
  total_tax: number;
  effective_rate: number;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost_basis: number;
  total_gain_loss: number;
  total_return_pct: number;
  allocation: Record<string, number>;
}

export interface GuideSection {
  title: string;
  content: string;
}

export interface DbStats {
  accounts: number;
  transactions: number;
  holdings: number;
  tax_documents: number;
  chat_sessions: number;
  audit_entries: number;
  budgets: number;
  goals: number;
  debts: number;
}
