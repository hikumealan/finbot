import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { FileImport } from "@/components/file-import";
import { formatCurrency } from "@/lib/utils";
import type { PortfolioSummary } from "@/types";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export const Route = createFileRoute("/investments")({ component: Investments });

function Investments() {
  const [showImport, setShowImport] = useState(false);
  const { data: ps } = useQuery<PortfolioSummary>({ queryKey: ["investments"], queryFn: () => api.get("/api/investments/summary") });
  const { data: rebalance } = useQuery({ queryKey: ["rebalance"], queryFn: () => api.get<Array<{ asset_class: string; current_pct: number; target_pct: number; drift: number; action: string; amount: number }>>("/api/investments/rebalance") });

  const [balance, setBalance] = useState(100000);
  const [er, setEr] = useState(0.85);
  const [years, setYears] = useState(30);
  const { data: feeData } = useQuery({
    queryKey: ["fee-impact", balance, er, years],
    queryFn: () => api.post<{ fee_drag: number; high_cost_final: number; low_cost_final: number }>("/api/investments/fee-impact", { balance, expense_ratio: er / 100, years }),
    enabled: balance > 0,
  });

  if (!ps) return <div>Loading...</div>;

  const allocData = Object.entries(ps.allocation).map(([name, value]) => ({ name, value }));
  const gainColor = ps.total_gain_loss >= 0 ? "text-green-600" : "text-red-600";

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Investments</h1>
        <button onClick={() => setShowImport(!showImport)} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md">{showImport ? "Hide" : "Import Brokerage Statement"}</button>
      </div>
      {showImport && <div className="bg-card p-4 rounded-lg border border-border"><FileImport type="statement" onSuccess={() => setShowImport(false)} /></div>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card p-4 rounded-lg border border-border"><p className="text-sm text-muted-foreground">Portfolio Value</p><p className="text-2xl font-bold">{formatCurrency(ps.total_value)}</p></div>
        <div className="bg-card p-4 rounded-lg border border-border"><p className="text-sm text-muted-foreground">Cost Basis</p><p className="text-2xl font-bold">{formatCurrency(ps.total_cost_basis)}</p></div>
        <div className="bg-card p-4 rounded-lg border border-border"><p className="text-sm text-muted-foreground">Gain/Loss</p><p className={`text-2xl font-bold ${gainColor}`}>{formatCurrency(ps.total_gain_loss)} ({ps.total_return_pct.toFixed(1)}%)</p></div>
      </div>

      {allocData.length > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Asset Allocation</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart><Pie data={allocData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={90} label>{allocData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {rebalance && rebalance.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
          <h3 className="font-semibold text-yellow-800 mb-2">Rebalancing Needed</h3>
          {rebalance.map((s) => <p key={s.asset_class} className="text-sm">{s.asset_class}: {s.current_pct.toFixed(1)}% → {s.target_pct.toFixed(1)}% — {s.action} {formatCurrency(s.amount)}</p>)}
        </div>
      )}

      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">Fee Impact Calculator</h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div><label className="text-sm text-muted-foreground">Balance ($)</label><input type="number" value={balance} onChange={(e) => setBalance(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Expense Ratio (%)</label><input type="number" value={er} onChange={(e) => setEr(+e.target.value)} step={0.05} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Years</label><input type="range" min={10} max={40} value={years} onChange={(e) => setYears(+e.target.value)} className="w-full" /><span className="text-sm">{years}</span></div>
        </div>
        {feeData && <p className="text-lg font-bold">Fee Drag: <span className="text-red-600">{formatCurrency(feeData.fee_drag)}</span> over {years} years</p>}
      </div>

      <HoldingsManager />
    </div>
  );
}

function HoldingsManager() {
  const qc = useQueryClient();
  const { data: holdings } = useQuery<Array<{ id: number; symbol: string; shares: number; cost_basis: number; current_price: number | null; asset_class: string }>>({ queryKey: ["holdings"], queryFn: () => api.get("/api/investments/holdings") });
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ symbol: "", shares: 0, cost_basis: 0, current_price: 0, asset_class: "equity" });

  const invalidate = () => { qc.invalidateQueries({ queryKey: ["holdings"] }); qc.invalidateQueries({ queryKey: ["investments"] }); };
  const addMut = useMutation({ mutationFn: (b: typeof form & { account_id: number }) => api.post("/api/investments/holdings", b), onSuccess: () => { invalidate(); setAdding(false); setForm({ symbol: "", shares: 0, cost_basis: 0, current_price: 0, asset_class: "equity" }); } });
  const deleteMut = useMutation({ mutationFn: (id: number) => api.delete(`/api/investments/holdings/${id}`), onSuccess: invalidate });

  return (
    <div className="bg-card p-4 rounded-lg border border-border">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">Holdings</h3>
        <button onClick={() => setAdding(!adding)} className="text-sm text-primary">{adding ? "Cancel" : "+ Add Holding"}</button>
      </div>

      {adding && (
        <div className="grid grid-cols-5 gap-2 mb-4">
          <input placeholder="Symbol" value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} className="border rounded px-2 py-1 text-sm" />
          <input type="number" placeholder="Shares" value={form.shares || ""} onChange={(e) => setForm({ ...form, shares: +e.target.value })} className="border rounded px-2 py-1 text-sm" />
          <input type="number" placeholder="Cost Basis" value={form.cost_basis || ""} onChange={(e) => setForm({ ...form, cost_basis: +e.target.value })} className="border rounded px-2 py-1 text-sm" />
          <input type="number" placeholder="Current Price" value={form.current_price || ""} onChange={(e) => setForm({ ...form, current_price: +e.target.value })} className="border rounded px-2 py-1 text-sm" />
          <button onClick={() => addMut.mutate({ ...form, account_id: 1 })} className="bg-primary text-primary-foreground px-3 py-1 rounded text-sm">Add</button>
        </div>
      )}

      {holdings && holdings.length > 0 ? (
        <div className="rounded-lg border border-border overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Symbol</th><th className="text-right px-4 py-2.5 font-medium">Shares</th><th className="text-right px-4 py-2.5 font-medium">Cost Basis</th><th className="text-right px-4 py-2.5 font-medium">Price</th><th className="text-left px-4 py-2.5 font-medium">Class</th><th className="px-4 py-2.5"></th></tr></thead>
            <tbody>{holdings.map((h) => (
              <tr key={h.id} className="border-b border-border hover:bg-accent/30">
                <td className="px-4 py-2.5 font-mono">{h.symbol}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">{h.shares}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(h.cost_basis)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">{h.current_price ? formatCurrency(h.current_price) : "—"}</td>
                <td className="px-4 py-2.5"><span className="text-xs bg-secondary px-2 py-0.5 rounded-full">{h.asset_class}</span></td>
                <td className="px-4 py-2.5"><div className="flex items-center justify-end"><button onClick={() => deleteMut.mutate(h.id)} className="text-xs text-destructive hover:text-red-700 active:text-red-700">Del</button></div></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : <p className="text-muted-foreground text-sm">No holdings. Import a brokerage statement or add manually.</p>}
    </div>
  );
}
