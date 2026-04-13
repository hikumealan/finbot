import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";
import type { DashboardSummary } from "@/types";

export const Route = createFileRoute("/report")({ component: Report });

function Report() {
  const { data } = useQuery<DashboardSummary>({ queryKey: ["dashboard"], queryFn: () => api.get("/api/dashboard/summary") });

  if (!data) return <p>Loading report...</p>;

  const cats = Object.entries(data.expenses_by_category).sort((a, b) => b[1] - a[1]);

  return (
    <div className="max-w-2xl mx-auto py-8 print:py-0 text-sm">
      <style>{`@media print { nav, aside, header, .no-print { display: none !important; } main { padding: 0 !important; } }`}</style>

      <h1 className="text-2xl font-bold mb-1">FinBot Financial Report</h1>
      <p className="text-muted-foreground mb-6">{new Date().toLocaleDateString()}</p>

      <section className="mb-6">
        <h2 className="text-lg font-semibold border-b pb-1 mb-3">Net Worth</h2>
        <table className="w-full"><tbody>
          <tr><td>Total Assets</td><td className="text-right">{formatCurrency(data.total_assets)}</td></tr>
          <tr><td>Total Liabilities</td><td className="text-right">{formatCurrency(data.total_liabilities)}</td></tr>
          <tr className="font-bold border-t"><td>Net Worth</td><td className="text-right">{formatCurrency(data.net_worth)}</td></tr>
        </tbody></table>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-semibold border-b pb-1 mb-3">Income & Expenses</h2>
        <table className="w-full"><tbody>
          <tr><td>Total Income</td><td className="text-right">{formatCurrency(data.total_income)}</td></tr>
          <tr><td>Total Expenses</td><td className="text-right">{formatCurrency(data.total_expenses)}</td></tr>
          <tr className="font-bold border-t"><td>Savings Rate</td><td className="text-right">{data.savings_rate.toFixed(1)}%</td></tr>
        </tbody></table>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-semibold border-b pb-1 mb-3">Expense Breakdown</h2>
        <table className="w-full"><tbody>
          {cats.map(([cat, amt]) => (
            <tr key={cat}><td>{cat}</td><td className="text-right">{formatCurrency(amt)}</td><td className="text-right text-muted-foreground w-16">{data.total_expenses > 0 ? ((amt / data.total_expenses) * 100).toFixed(0) : 0}%</td></tr>
          ))}
        </tbody></table>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-semibold border-b pb-1 mb-3">Emergency Fund</h2>
        <p>Coverage: {data.emergency_fund_months === -1 ? "N/A" : `${data.emergency_fund_months.toFixed(1)} months`}</p>
        <p>Liquid Savings: {formatCurrency(data.liquid_savings)}</p>
      </section>

      <p className="text-xs text-muted-foreground mt-8 border-t pt-4">This report is for informational purposes only and does not constitute financial advice.</p>

      <button onClick={() => window.print()} className="no-print mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm">
        Print / Save as PDF
      </button>
    </div>
  );
}
