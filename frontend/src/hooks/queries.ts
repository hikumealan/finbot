import { queryOptions } from "@tanstack/react-query";
import { api } from "@/api/client";

export const queryKeys = {
  dashboard: ["dashboard"] as const,
  expenses: (month?: string) => ["expenses", { month }] as const,
  expensesByMonth: ["expenses", "by-month"] as const,
  subscriptions: ["subscriptions"] as const,
  transactions: (filters?: Record<string, unknown>) => ["transactions", filters] as const,
  budgets: ["budgets"] as const,
  budgetVariance: (month?: string) => ["budgets", "variance", { month }] as const,
  accounts: ["accounts"] as const,
  investments: ["investments"] as const,
  rebalance: ["rebalance"] as const,
  muniHoldings: ["munis", "holdings"] as const,
  debts: ["debts"] as const,
  debtCompare: (extra?: number) => ["debts", "compare", { extra }] as const,
  goals: ["goals"] as const,
  taxPosition: (year?: number) => ["tax", "position", { year }] as const,
  taxTlh: ["tax", "tlh"] as const,
  taxDocuments: ["tax", "documents"] as const,
  chatSessions: (type?: string) => ["chat", "sessions", { type }] as const,
  chatMessages: (id: number) => ["chat", "messages", id] as const,
  profile: ["settings", "profile"] as const,
  stats: ["settings", "stats"] as const,
  config: ["config"] as const,
  backups: ["backups"] as const,
  importHistory: ["import", "history"] as const,
  guideSections: ["guide", "sections"] as const,
};

export const dashboardQuery = queryOptions({
  queryKey: queryKeys.dashboard,
  queryFn: () => api.get("/api/dashboard/summary"),
});

export const accountsQuery = queryOptions({
  queryKey: queryKeys.accounts,
  queryFn: () => api.get("/api/accounts"),
});

export const statsQuery = queryOptions({
  queryKey: queryKeys.stats,
  queryFn: () => api.get("/api/settings/stats"),
});
