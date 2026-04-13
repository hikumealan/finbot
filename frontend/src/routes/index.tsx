import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { FileImport } from "@/components/file-import";
import { formatCurrency } from "@/lib/utils";
import type { DashboardSummary } from "@/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

export const Route = createFileRoute("/")({
  component: Dashboard,
});

function Dashboard() {
  const [showImport, setShowImport] = useState(false);
  const { data, isLoading } = useQuery<DashboardSummary>({
    queryKey: ["dashboard"],
    queryFn: () => api.get("/api/dashboard/summary"),
  });

  if (isLoading || !data) return <div className="animate-pulse">Loading...</div>;

  const catData = Object.entries(data.expenses_by_category).map(([name, value]) => ({ name, value }));
  const monthData = Object.entries(data.expenses_by_month).map(([month, amount]) => ({ month, amount }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button onClick={() => setShowImport(!showImport)} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md">
          {showImport ? "Hide Import" : "Import Statement"}
        </button>
      </div>

      {showImport && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Import Financial Statement</h3>
          <FileImport type="statement" onSuccess={() => setShowImport(false)} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard label="Net Worth" value={formatCurrency(data.net_worth)} />
        <MetricCard label="Total Income" value={formatCurrency(data.total_income)} />
        <MetricCard label="Total Expenses" value={formatCurrency(data.total_expenses)} />
        <MetricCard label="Savings Rate" value={`${data.savings_rate.toFixed(1)}%`} />
      </div>

      {data.emergency_fund_months > 0 && data.emergency_fund_months !== -1 && (
        <div className={`p-3 rounded-md text-sm ${data.emergency_fund_months < 3 ? "bg-red-100 text-red-800" : data.emergency_fund_months < 6 ? "bg-yellow-100 text-yellow-800" : "bg-green-100 text-green-800"}`}>
          Emergency Fund: {data.emergency_fund_months.toFixed(1)} months of expenses
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {monthData.length > 0 && (
          <div className="bg-card p-4 rounded-lg border border-border">
            <h3 className="font-semibold mb-3">Monthly Expenses</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={monthData}>
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
                <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {catData.length > 0 && (
          <div className="bg-card p-4 rounded-lg border border-border">
            <h3 className="font-semibold mb-3">Expense Categories</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={catData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card p-4 rounded-lg border border-border">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}
