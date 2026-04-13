import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { FileImport } from "@/components/file-import";
import { formatCurrency } from "@/lib/utils";
import type { Transaction } from "@/types";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

export const Route = createFileRoute("/expenses")({ component: Expenses });

function Expenses() {
  const [tab, setTab] = useState<"categories" | "budget" | "subscriptions" | "transactions">("categories");
  const [showImport, setShowImport] = useState(false);
  const tabs = ["categories", "budget", "subscriptions", "transactions"] as const;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Expenses & Budget</h1>
        <button onClick={() => setShowImport(!showImport)} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md">
          {showImport ? "Hide" : "Import Statement"}
        </button>
      </div>
      {showImport && <div className="bg-card p-4 rounded-lg border border-border"><FileImport type="statement" onSuccess={() => setShowImport(false)} /></div>}
      <div className="flex border-b border-border">
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm -mb-px border-b-2 transition-colors ${tab === t ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"}`}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>
      {tab === "categories" && <CategoriesTab />}
      {tab === "budget" && <BudgetTab />}
      {tab === "subscriptions" && <SubscriptionsTab />}
      {tab === "transactions" && <TransactionsTab />}
    </div>
  );
}

function CategoriesTab() {
  const { data } = useQuery({ queryKey: ["expenses"], queryFn: () => api.get<{ total: number; by_category: Record<string, number> }>("/api/expenses") });
  const { data: monthly } = useQuery({ queryKey: ["expenses", "by-month"], queryFn: () => api.get<Record<string, number>>("/api/expenses/by-month") });

  if (!data) return <div>Loading...</div>;
  const catData = Object.entries(data.by_category).map(([name, value]) => ({ name, value }));
  const monthData = monthly ? Object.entries(monthly).map(([month, amount]) => ({ month, amount })) : [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">By Category (Total: {formatCurrency(data.total)})</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart><Pie data={catData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={80} label>{catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip formatter={(v: number) => formatCurrency(v)} /></PieChart>
        </ResponsiveContainer>
      </div>
      {monthData.length > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Monthly Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthData}><XAxis dataKey="month" /><YAxis /><Tooltip formatter={(v: number) => formatCurrency(v)} /><Bar dataKey="amount" fill="#3b82f6" /></BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function BudgetTab() {
  const { data } = useQuery({ queryKey: ["budgets", "variance"], queryFn: () => api.get<Array<{ category: string; budget: number; actual: number; variance: number; pct: number; is_over: boolean }>>("/api/budgets/variance") });
  const qc = useQueryClient();
  const [cat, setCat] = useState("");
  const [amt, setAmt] = useState(0);
  const addBudget = useMutation({ mutationFn: (b: { category: string; monthly_limit: number }) => api.post("/api/budgets", b), onSuccess: () => qc.invalidateQueries({ queryKey: ["budgets"] }) });

  if (!data) return <div>Loading...</div>;
  return (
    <div className="space-y-4">
      {data.length === 0 ? <p className="text-muted-foreground">No budgets set yet.</p> : data.map((v) => (
        <div key={v.category} className={`p-3 rounded-md border ${v.is_over ? "border-red-300 bg-red-50" : "border-green-300 bg-green-50"}`}>
          <div className="flex justify-between"><span className="font-medium">{v.category}</span><span>{formatCurrency(v.actual)} / {formatCurrency(v.budget)}</span></div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2"><div className={`h-2 rounded-full ${v.is_over ? "bg-red-500" : "bg-green-500"}`} style={{ width: `${Math.min(v.pct, 100)}%` }} /></div>
        </div>
      ))}
      <div className="bg-card p-4 rounded-lg border border-border">
        <h4 className="font-medium mb-2">Add Budget Target</h4>
        <div className="flex gap-2">
          <input placeholder="Category" value={cat} onChange={(e) => setCat(e.target.value)} className="border rounded px-2 py-1 flex-1" />
          <input type="number" placeholder="Monthly limit" value={amt || ""} onChange={(e) => setAmt(+e.target.value)} className="border rounded px-2 py-1 w-32" />
          <button onClick={() => { if (cat && amt > 0) { addBudget.mutate({ category: cat, monthly_limit: amt }); setCat(""); setAmt(0); } }} className="bg-primary text-primary-foreground px-3 py-1 rounded-md text-sm">Add</button>
        </div>
      </div>
    </div>
  );
}

function SubscriptionsTab() {
  const { data } = useQuery({ queryKey: ["subscriptions"], queryFn: () => api.get<Array<{ description: string; amount: number; frequency: number }>>("/api/expenses/subscriptions") });
  if (!data || data.length === 0) return <p className="text-muted-foreground">Not enough data to detect subscriptions.</p>;
  const total = data.reduce((s, v) => s + v.amount, 0);
  return (
    <div>
      <p className="text-lg font-bold mb-4">Total Recurring: {formatCurrency(total)}/month</p>
      <div className="bg-card rounded-lg border border-border overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Description</th><th className="text-right px-4 py-2.5 font-medium">Amount</th><th className="text-right px-4 py-2.5 font-medium">Months</th></tr></thead>
          <tbody>{data.map((s, i) => <tr key={i} className="border-b border-border hover:bg-accent/30"><td className="px-4 py-2.5">{s.description}</td><td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(s.amount)}</td><td className="px-4 py-2.5 text-right tabular-nums">{s.frequency}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}

function TransactionsTab() {
  const qc = useQueryClient();
  const { data } = useQuery<Transaction[]>({ queryKey: ["transactions"], queryFn: () => api.get("/api/transactions?limit=50") });
  const [editing, setEditing] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Record<string, string | number>>({});

  const invalidateAll = () => { qc.invalidateQueries({ queryKey: ["transactions"] }); qc.invalidateQueries({ queryKey: ["expenses"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); };

  const saveMut = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) => api.patch(`/api/transactions/${id}`, body),
    onSuccess: () => { invalidateAll(); setEditing(null); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => api.delete(`/api/transactions/${id}`),
    onSuccess: invalidateAll,
  });

  const startEdit = (tx: Transaction) => {
    setEditing(tx.id);
    setEditForm({ category: tx.category || "", subcategory: tx.subcategory || "", description: tx.description, amount: tx.amount, tx_type: tx.tx_type });
  };

  if (!data) return <div>Loading...</div>;
  return (
    <div className="bg-card rounded-lg border border-border overflow-x-auto">
      <table className="w-full text-sm">
        <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Date</th><th className="text-left px-4 py-2.5 font-medium">Description</th><th className="text-left px-4 py-2.5 font-medium">Category</th><th className="text-right px-4 py-2.5 font-medium">Amount</th><th className="text-left px-4 py-2.5 font-medium">Type</th><th className="px-4 py-2.5"></th></tr></thead>
        <tbody>
          {data.map((tx) => (
            <tr key={tx.id} className="border-b border-border hover:bg-accent/30">
              {editing === tx.id ? (
                <>
                  <td className="px-4 py-2.5">{tx.date}</td>
                  <td className="px-4 py-2.5"><input value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} className="w-full border border-input rounded-md px-2 py-1 text-sm bg-background" /></td>
                  <td className="px-4 py-2.5"><input value={editForm.category} onChange={(e) => setEditForm({ ...editForm, category: e.target.value })} className="w-full border border-input rounded-md px-2 py-1 text-sm bg-background" /></td>
                  <td className="px-4 py-2.5"><input type="number" value={editForm.amount} onChange={(e) => setEditForm({ ...editForm, amount: +e.target.value })} className="w-20 border border-input rounded-md px-2 py-1 text-sm text-right bg-background" /></td>
                  <td className="px-4 py-2.5"><select value={editForm.tx_type} onChange={(e) => setEditForm({ ...editForm, tx_type: e.target.value })} className="border border-input rounded-md px-2 py-1 text-xs bg-background">{["expense", "income", "transfer"].map((t) => <option key={t} value={t}>{t}</option>)}</select></td>
                  <td className="px-4 py-2.5"><div className="flex items-center justify-end gap-1"><button onClick={() => saveMut.mutate({ id: tx.id, body: editForm })} className="text-xs text-primary font-medium">Save</button><button onClick={() => setEditing(null)} className="text-xs text-muted-foreground">Cancel</button></div></td>
                </>
              ) : (
                <>
                  <td className="px-4 py-2.5">{tx.date}</td>
                  <td className="px-4 py-2.5">{tx.description}</td>
                  <td className="px-4 py-2.5">{tx.category || "—"}</td>
                  <td className={`px-4 py-2.5 text-right tabular-nums ${tx.amount < 0 ? "text-red-600" : "text-green-600"}`}>{formatCurrency(tx.amount)}</td>
                  <td className="px-4 py-2.5"><span className="text-xs bg-secondary px-2 py-0.5 rounded-full">{tx.tx_type}</span></td>
                  <td className="px-4 py-2.5"><div className="flex items-center justify-end gap-1"><button onClick={() => startEdit(tx)} className="text-xs text-muted-foreground hover:text-primary active:text-primary">Edit</button><button onClick={() => { if (confirm("Delete this transaction?")) deleteMut.mutate(tx.id); }} className="text-xs text-destructive hover:text-red-700 active:text-red-700">Del</button></div></td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
