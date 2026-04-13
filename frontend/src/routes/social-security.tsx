import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";

interface SSEstimate {
  claiming_age: number;
  monthly_benefit: number;
  annual_benefit: number;
  adjustment_pct: number;
}

interface SSOptResult {
  estimates: SSEstimate[];
  break_even_ages: Record<string, number | null>;
  optimal_age: number;
  optimal_monthly: number;
  lifetime_benefits: Record<number, number>;
  recommendation: string;
  spousal_benefit: number | null;
}

export const Route = createFileRoute("/social-security")({ component: SocialSecurity });

function SocialSecurity() {
  const [tab, setTab] = useState<"estimator" | "optimizer">("estimator");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Social Security</h1>
      <div className="flex border-b border-border">
        {(["estimator", "optimizer"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm -mb-px border-b-2 transition-colors capitalize ${tab === t ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"}`}>{t}</button>
        ))}
      </div>
      {tab === "estimator" ? <EstimatorTab /> : <OptimizerTab />}
    </div>
  );
}

function EstimatorTab() {
  const [salary, setSalary] = useState(75000);
  const [years, setYears] = useState(35);
  const [birthYear, setBirthYear] = useState(1990);

  const estimate = useMutation({
    mutationFn: () => api.post<SSEstimate[]>("/api/social-security/estimate", { annual_salary: salary, years_worked: years, birth_year: birthYear }),
  });

  return (
    <div className="space-y-6">
      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">Benefit Estimator</h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div><label className="text-sm text-muted-foreground">Annual Salary ($)</label><input type="number" value={salary} onChange={(e) => setSalary(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Years Worked</label><input type="number" value={years} onChange={(e) => setYears(+e.target.value)} min={0} max={45} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Birth Year</label><input type="number" value={birthYear} onChange={(e) => setBirthYear(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
        </div>
        <button onClick={() => estimate.mutate()} className="bg-primary text-primary-foreground px-4 py-2 rounded-md">Estimate Benefits</button>
      </div>

      {estimate.data && (
        <>
          <div className="bg-card p-4 rounded-lg border border-border">
            <h3 className="font-semibold mb-3">Monthly Benefit by Claiming Age</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={estimate.data}>
                <XAxis dataKey="claiming_age" />
                <YAxis tickFormatter={(v) => `$${v.toLocaleString()}`} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
                <Bar dataKey="monthly_benefit" radius={[4, 4, 0, 0]}>
                  {estimate.data.map((e, i) => <Cell key={i} fill={e.claiming_age === 67 ? "#10b981" : e.claiming_age === 70 ? "#3b82f6" : "#6b7280"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-card rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Claiming Age</th><th className="text-right px-4 py-2.5 font-medium">Monthly</th><th className="text-right px-4 py-2.5 font-medium">Annual</th><th className="text-right px-4 py-2.5 font-medium">Adjustment</th></tr></thead>
              <tbody>{estimate.data.map((e) => (
                <tr key={e.claiming_age} className={`border-b border-border hover:bg-accent/30 ${e.claiming_age === 67 ? "bg-green-50 font-medium" : ""}`}>
                  <td className="px-4 py-2.5">{e.claiming_age}{e.claiming_age === 67 ? " (FRA)" : ""}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(e.monthly_benefit)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(e.annual_benefit)}</td>
                  <td className={`px-4 py-2.5 text-right tabular-nums ${e.adjustment_pct < 0 ? "text-red-600" : e.adjustment_pct > 0 ? "text-green-600" : ""}`}>{e.adjustment_pct > 0 ? "+" : ""}{e.adjustment_pct}%</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function OptimizerTab() {
  const [salary, setSalary] = useState(75000);
  const [years, setYears] = useState(35);
  const [age, setAge] = useState(40);
  const [lifeExp, setLifeExp] = useState(85);
  const [spouseSalary, setSpouseSalary] = useState(0);
  const [otherIncome, setOtherIncome] = useState(0);

  const optimize = useMutation({
    mutationFn: () => api.post<SSOptResult>("/api/social-security/optimize", {
      annual_salary: salary, years_worked: years, current_age: age,
      life_expectancy: lifeExp, spouse_salary: spouseSalary || undefined,
      spouse_years_worked: spouseSalary ? 30 : undefined, other_annual_income: otherIncome,
    }),
  });

  const lifetimeData = optimize.data ? Object.entries(optimize.data.lifetime_benefits).map(([age, total]) => ({ age: +age, total })) : [];

  return (
    <div className="space-y-6">
      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">Claiming Strategy Optimizer</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <div><label className="text-sm text-muted-foreground">Annual Salary ($)</label><input type="number" value={salary} onChange={(e) => setSalary(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Years Worked</label><input type="number" value={years} onChange={(e) => setYears(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Current Age</label><input type="number" value={age} onChange={(e) => setAge(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Life Expectancy: {lifeExp}</label><input type="range" min={70} max={100} value={lifeExp} onChange={(e) => setLifeExp(+e.target.value)} className="w-full" /></div>
          <div><label className="text-sm text-muted-foreground">Spouse Salary ($, 0 if none)</label><input type="number" value={spouseSalary} onChange={(e) => setSpouseSalary(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm text-muted-foreground">Other Retirement Income ($/yr)</label><input type="number" value={otherIncome} onChange={(e) => setOtherIncome(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
        </div>
        <button onClick={() => optimize.mutate()} className="bg-primary text-primary-foreground px-4 py-2 rounded-md">Analyze</button>
      </div>

      {optimize.data && (
        <>
          <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-1">Recommendation: Claim at age {optimize.data.optimal_age}</h3>
            <p className="text-sm text-green-700">{optimize.data.recommendation}</p>
            {optimize.data.spousal_benefit && <p className="text-sm text-green-700 mt-2">Spousal benefit option: {formatCurrency(optimize.data.spousal_benefit)}/month</p>}
          </div>

          <div className="grid grid-cols-3 gap-4">
            {Object.entries(optimize.data.break_even_ages).map(([key, age]) => (
              <div key={key} className="bg-card p-3 rounded-lg border border-border">
                <p className="text-xs text-muted-foreground">{key.replace(/_/g, " ").replace("vs", " vs ")}</p>
                <p className="text-lg font-bold">{age ? `Age ${age}` : "N/A"}</p>
              </div>
            ))}
          </div>

          {lifetimeData.length > 0 && (
            <div className="bg-card p-4 rounded-lg border border-border">
              <h3 className="font-semibold mb-3">Total Lifetime Benefits by Claiming Age</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={lifetimeData}>
                  <XAxis dataKey="age" />
                  <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} />
                  <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                    {lifetimeData.map((d, i) => <Cell key={i} fill={d.age === optimize.data!.optimal_age ? "#10b981" : "#3b82f6"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
