import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";
import { US_STATES, FILING_STATUSES } from "@/lib/constants";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#3b82f6", "#ef4444", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];
const PAY_FREQUENCIES = [
  { value: "weekly", label: "Weekly (52)" },
  { value: "biweekly", label: "Bi-weekly (26)" },
  { value: "semimonthly", label: "Semi-monthly (24)" },
  { value: "monthly", label: "Monthly (12)" },
];

interface PayLine { label: string; annual: number; per_period: number; pct_of_gross: number }
interface AnalyzeResult { lines: PayLine[]; effective_tax_rate: number }
interface CompareResult { comparison: Array<{ label: string; current_annual: number; proposed_annual: number; delta_annual: number; current_per_period: number; proposed_per_period: number; delta_per_period: number }>; current_effective_rate: number; proposed_effective_rate: number; net_pay_change_annual: number }

export const Route = createFileRoute("/paycheck")({ component: Paycheck });

function Paycheck() {
  const [tab, setTab] = useState<"analyzer" | "planner">("analyzer");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Paycheck</h1>
      <div className="flex border-b border-border">
        {(["analyzer", "planner"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm -mb-px border-b-2 transition-colors capitalize ${tab === t ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"}`}>{t}</button>
        ))}
      </div>
      {tab === "analyzer" ? <AnalyzerTab /> : <PlannerTab />}
    </div>
  );
}

function usePaycheckForm() {
  const [form, setForm] = useState({
    gross_salary: 75000, pay_frequency: "biweekly", filing_status: "single",
    state: "" as string, k401_pct: 6, hsa_annual: 0, insurance_annual: 2400,
  });
  const set = (key: string, value: string | number) => setForm({ ...form, [key]: value });
  return { form, set, setForm };
}

function PaycheckForm({ form, set }: { form: ReturnType<typeof usePaycheckForm>["form"]; set: (k: string, v: string | number) => void }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div><label className="text-sm text-muted-foreground">Gross Salary ($/yr)</label><input type="number" value={form.gross_salary} onChange={(e) => set("gross_salary", +e.target.value)} className="w-full border rounded px-2 py-1" /></div>
      <div><label className="text-sm text-muted-foreground">Pay Frequency</label><select value={form.pay_frequency} onChange={(e) => set("pay_frequency", e.target.value)} className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background">{PAY_FREQUENCIES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}</select></div>
      <div><label className="text-sm text-muted-foreground">Filing Status</label><select value={form.filing_status} onChange={(e) => set("filing_status", e.target.value)} className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background">{FILING_STATUSES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}</select></div>
      <div><label className="text-sm text-muted-foreground">State</label><select value={form.state} onChange={(e) => set("state", e.target.value)} className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"><option value="">None</option>{US_STATES.map((s) => <option key={s}>{s}</option>)}</select></div>
      <div><label className="text-sm text-muted-foreground">401(k) %</label><input type="number" value={form.k401_pct} onChange={(e) => set("k401_pct", +e.target.value)} min={0} max={100} step={1} className="w-full border rounded px-2 py-1" /></div>
      <div><label className="text-sm text-muted-foreground">HSA ($/yr)</label><input type="number" value={form.hsa_annual} onChange={(e) => set("hsa_annual", +e.target.value)} className="w-full border rounded px-2 py-1" /></div>
      <div><label className="text-sm text-muted-foreground">Insurance ($/yr)</label><input type="number" value={form.insurance_annual} onChange={(e) => set("insurance_annual", +e.target.value)} className="w-full border rounded px-2 py-1" /></div>
    </div>
  );
}

function AnalyzerTab() {
  const { form, set } = usePaycheckForm();
  const analyze = useMutation({ mutationFn: () => api.post<AnalyzeResult>("/api/paycheck/analyze", form) });

  const deductions = analyze.data?.lines.filter((l) => l.annual < 0).map((l) => ({ name: l.label, value: Math.abs(l.annual) })) || [];

  return (
    <div className="space-y-6">
      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">Paycheck Breakdown</h3>
        <PaycheckForm form={form} set={set} />
        <button onClick={() => analyze.mutate()} className="mt-4 bg-primary text-primary-foreground px-4 py-2 rounded-md">Analyze</button>
      </div>

      {analyze.data && (
        <>
          <div className="bg-card p-3 rounded-lg border border-border"><p className="text-sm">Effective Tax Rate: <span className="font-bold">{analyze.data.effective_tax_rate}%</span></p></div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-card rounded-lg border border-border overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Item</th><th className="text-right px-4 py-2.5 font-medium">Per Period</th><th className="text-right px-4 py-2.5 font-medium">Annual</th><th className="text-right px-4 py-2.5 font-medium">% of Gross</th></tr></thead>
                <tbody>{analyze.data.lines.map((l) => (
                  <tr key={l.label} className={`border-b border-border hover:bg-accent/30 ${l.label === "Net Pay" || l.label === "Gross Pay" ? "font-bold" : ""}`}>
                    <td className="px-4 py-2.5">{l.label}</td>
                    <td className={`px-4 py-2.5 text-right tabular-nums ${l.annual < 0 ? "text-red-600" : ""}`}>{formatCurrency(l.per_period)}</td>
                    <td className={`px-4 py-2.5 text-right tabular-nums ${l.annual < 0 ? "text-red-600" : ""}`}>{formatCurrency(l.annual)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">{Math.abs(l.pct_of_gross)}%</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>

            {deductions.length > 0 && (
              <div className="bg-card p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2 text-sm">Where Your Paycheck Goes</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart><Pie data={deductions} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>{deductions.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip formatter={(v: number) => formatCurrency(v)} /></PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function PlannerTab() {
  const { form: currentForm, set: setCurrent, setForm: setCurrentForm } = usePaycheckForm();
  const { form: proposedForm, set: setProposed, setForm: setProposedForm } = usePaycheckForm();

  const compare = useMutation({
    mutationFn: () => api.post<CompareResult>("/api/paycheck/compare", { current: currentForm, proposed: proposedForm }),
  });

  const presets = [
    { label: "Max 401k (15%)", apply: () => setProposedForm({ ...proposedForm, k401_pct: 15 }) },
    { label: "Max HSA ($4,300)", apply: () => setProposedForm({ ...proposedForm, hsa_annual: 4300 }) },
    { label: "$10k Raise", apply: () => setProposedForm({ ...proposedForm, gross_salary: proposedForm.gross_salary + 10000 }) },
    { label: "MFJ Status", apply: () => setProposedForm({ ...proposedForm, filing_status: "married_joint" }) },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Current</h3>
          <PaycheckForm form={currentForm} set={setCurrent} />
        </div>
        <div className="bg-card p-4 rounded-lg border border-border">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold">Proposed</h3>
            <button onClick={() => setProposedForm({ ...currentForm })} className="text-xs text-primary">Copy from Current</button>
          </div>
          <PaycheckForm form={proposedForm} set={setProposed} />
          <div className="flex flex-wrap gap-1 mt-3">
            {presets.map((p) => <button key={p.label} onClick={p.apply} className="text-xs px-2 py-1 border rounded hover:bg-accent">{p.label}</button>)}
          </div>
        </div>
      </div>

      <button onClick={() => compare.mutate()} className="bg-primary text-primary-foreground px-4 py-2 rounded-md">Compare</button>

      {compare.data && (
        <>
          <div className={`p-3 rounded-lg border ${compare.data.net_pay_change_annual >= 0 ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
            <p className="font-bold">Net pay change: <span className={compare.data.net_pay_change_annual >= 0 ? "text-green-700" : "text-red-700"}>{compare.data.net_pay_change_annual >= 0 ? "+" : ""}{formatCurrency(compare.data.net_pay_change_annual)}/year</span></p>
            <p className="text-sm">Tax rate: {compare.data.current_effective_rate}% → {compare.data.proposed_effective_rate}%</p>
          </div>

          <div className="bg-card rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Item</th><th className="text-right px-4 py-2.5 font-medium">Current</th><th className="text-right px-4 py-2.5 font-medium">Proposed</th><th className="text-right px-4 py-2.5 font-medium">Change</th></tr></thead>
              <tbody>{compare.data.comparison.map((c) => (
                <tr key={c.label} className={`border-b border-border hover:bg-accent/30 ${c.label === "Net Pay" || c.label === "Gross Pay" ? "font-bold" : ""}`}>
                  <td className="px-4 py-2.5">{c.label}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(c.current_annual)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(c.proposed_annual)}</td>
                  <td className={`px-4 py-2.5 text-right tabular-nums font-medium ${c.delta_annual > 0 ? "text-green-600" : c.delta_annual < 0 ? "text-red-600" : ""}`}>
                    {c.delta_annual !== 0 ? `${c.delta_annual > 0 ? "+" : ""}${formatCurrency(c.delta_annual)}` : "—"}
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
