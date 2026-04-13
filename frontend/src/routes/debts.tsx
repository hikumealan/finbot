import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";
import type { Debt } from "@/types";

export const Route = createFileRoute("/debts")({ component: Debts });

function Debts() {
  const qc = useQueryClient();
  const { data: debts } = useQuery<Debt[]>({ queryKey: ["debts"], queryFn: () => api.get("/api/debts") });
  const [extra, setExtra] = useState(0);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", principal: 0, interest_rate: 0, minimum_payment: 0, debt_type: "credit_card" });
  const { data: compare } = useQuery({
    queryKey: ["debts", "compare", extra],
    queryFn: () => api.get<{ avalanche: Array<{ name: string; months: number; interest: number }>; snowball: Array<{ name: string; months: number; interest: number }>; interest_saved: number }>(`/api/debts/compare?extra_payment=${extra}`),
    enabled: !!debts && debts.length > 0,
  });

  const invalidate = () => { qc.invalidateQueries({ queryKey: ["debts"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); };
  const addMut = useMutation({ mutationFn: (b: typeof form) => api.post("/api/debts", b), onSuccess: () => { invalidate(); setAdding(false); setForm({ name: "", principal: 0, interest_rate: 0, minimum_payment: 0, debt_type: "credit_card" }); } });
  const editMut = useMutation({ mutationFn: ({ id, body }: { id: number; body: typeof form }) => api.patch(`/api/debts/${id}`, body), onSuccess: () => { invalidate(); setEditing(null); } });
  const deleteMut = useMutation({ mutationFn: (id: number) => api.delete(`/api/debts/${id}`), onSuccess: invalidate });

  const startEdit = (d: Debt) => { setEditing(d.id); setForm({ name: d.name, principal: d.principal, interest_rate: d.interest_rate * 100, minimum_payment: d.minimum_payment, debt_type: d.debt_type }); };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Debt Payoff Planner</h1>
        <button onClick={() => setAdding(!adding)} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md">{adding ? "Cancel" : "+ Add Debt"}</button>
      </div>

      {adding && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-medium mb-3">Add Debt</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="border rounded px-2 py-1" />
            <input type="number" placeholder="Principal ($)" value={form.principal || ""} onChange={(e) => setForm({ ...form, principal: +e.target.value })} className="border rounded px-2 py-1" />
            <input type="number" placeholder="Rate (%)" value={form.interest_rate || ""} onChange={(e) => setForm({ ...form, interest_rate: +e.target.value })} step={0.25} className="border rounded px-2 py-1" />
            <input type="number" placeholder="Min Payment ($)" value={form.minimum_payment || ""} onChange={(e) => setForm({ ...form, minimum_payment: +e.target.value })} className="border rounded px-2 py-1" />
            <select value={form.debt_type} onChange={(e) => setForm({ ...form, debt_type: e.target.value })} className="border border-input rounded-md px-3 py-2 text-sm bg-background">{["mortgage", "student", "auto", "credit_card"].map((t) => <option key={t} value={t}>{t}</option>)}</select>
          </div>
          <button onClick={() => { if (form.name) addMut.mutate({ ...form, interest_rate: form.interest_rate / 100 }); }} className="mt-3 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm">Save</button>
        </div>
      )}

      {debts && debts.length > 0 ? (
        <>
          <div className="bg-card rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Name</th><th className="text-right px-4 py-2.5 font-medium">Balance</th><th className="text-right px-4 py-2.5 font-medium">Rate</th><th className="text-right px-4 py-2.5 font-medium">Min Payment</th><th className="text-left px-4 py-2.5 font-medium">Type</th><th className="px-4 py-2.5"></th></tr></thead>
              <tbody>{debts.map((d) => (
                <tr key={d.id} className="border-b border-border hover:bg-accent/30">
                  {editing === d.id ? (
                    <>
                      <td className="px-4 py-2.5"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-input rounded-md px-2 py-1 text-sm bg-background" /></td>
                      <td className="px-4 py-2.5"><input type="number" value={form.principal} onChange={(e) => setForm({ ...form, principal: +e.target.value })} className="w-24 border border-input rounded-md px-2 py-1 text-sm text-right bg-background" /></td>
                      <td className="px-4 py-2.5"><input type="number" value={form.interest_rate} onChange={(e) => setForm({ ...form, interest_rate: +e.target.value })} step={0.25} className="w-20 border border-input rounded-md px-2 py-1 text-sm text-right bg-background" /></td>
                      <td className="px-4 py-2.5"><input type="number" value={form.minimum_payment} onChange={(e) => setForm({ ...form, minimum_payment: +e.target.value })} className="w-24 border border-input rounded-md px-2 py-1 text-sm text-right bg-background" /></td>
                      <td className="px-4 py-2.5"><select value={form.debt_type} onChange={(e) => setForm({ ...form, debt_type: e.target.value })} className="border border-input rounded-md px-2 py-1 text-xs bg-background">{["mortgage", "student", "auto", "credit_card"].map((t) => <option key={t}>{t}</option>)}</select></td>
                      <td className="px-4 py-2.5"><div className="flex items-center justify-end gap-1"><button onClick={() => editMut.mutate({ id: d.id, body: { ...form, interest_rate: form.interest_rate / 100 } })} className="text-xs text-primary font-medium">Save</button><button onClick={() => setEditing(null)} className="text-xs text-muted-foreground">Cancel</button></div></td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-2.5 font-medium">{d.name}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(d.principal)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{(d.interest_rate * 100).toFixed(2)}%</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(d.minimum_payment)}</td>
                      <td className="px-4 py-2.5"><span className="text-xs bg-secondary px-2 py-0.5 rounded-full">{d.debt_type}</span></td>
                      <td className="px-4 py-2.5"><div className="flex items-center justify-end gap-1"><button onClick={() => startEdit(d)} className="text-xs text-muted-foreground hover:text-primary active:text-primary">Edit</button><button onClick={() => deleteMut.mutate(d.id)} className="text-xs text-destructive hover:text-red-700 active:text-red-700">Del</button></div></td>
                    </>
                  )}
                </tr>
              ))}</tbody>
            </table>
          </div>

          <div><label className="text-sm font-medium">Extra Monthly Payment: {formatCurrency(extra)}</label><input type="range" min={0} max={2000} step={50} value={extra} onChange={(e) => setExtra(+e.target.value)} className="w-full" /></div>

          {compare && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-card p-4 rounded-lg border border-border"><h3 className="font-semibold mb-2">Avalanche</h3>{compare.avalanche.map((r) => <p key={r.name} className="text-sm">{r.name}: {r.months} mo, {formatCurrency(r.interest)} interest</p>)}</div>
              <div className="bg-card p-4 rounded-lg border border-border"><h3 className="font-semibold mb-2">Snowball</h3>{compare.snowball.map((r) => <p key={r.name} className="text-sm">{r.name}: {r.months} mo, {formatCurrency(r.interest)} interest</p>)}</div>
            </div>
          )}
          {compare && <p className="text-green-600 font-medium">Avalanche saves {formatCurrency(compare.interest_saved)}</p>}
        </>
      ) : <p className="text-muted-foreground">No debts tracked. Click "+ Add Debt" to get started.</p>}
    </div>
  );
}
