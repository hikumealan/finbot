import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export const Route = createFileRoute("/projections")({ component: Projections });

function Projections() {
  const [initial, setInitial] = useState(100000);
  const [annual, setAnnual] = useState(12000);
  const [years, setYears] = useState(30);
  const [inflation, setInflation] = useState(3);
  const [showReal, setShowReal] = useState(true);

  const { data } = useQuery({
    queryKey: ["projections", initial, annual, years, inflation],
    queryFn: () => api.post<{ years: number; nominal: number[]; real: number[]; percentiles: Record<number, number> }>("/api/projections/monte-carlo", { initial, annual_contribution: annual, years, inflation: inflation / 100 }),
  });

  const chartData = data ? (showReal ? data.real : data.nominal).map((v, i) => ({ year: i + 1, value: v })) : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Growth Projections</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div><label className="text-sm text-muted-foreground">Starting Balance ($)</label><input type="number" value={initial} onChange={(e) => setInitial(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
        <div><label className="text-sm text-muted-foreground">Annual Contribution ($)</label><input type="number" value={annual} onChange={(e) => setAnnual(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
        <div><label className="text-sm text-muted-foreground">Years: {years}</label><input type="range" min={5} max={50} value={years} onChange={(e) => setYears(+e.target.value)} className="w-full" /></div>
        <div><label className="text-sm text-muted-foreground">Inflation: {inflation}%</label><input type="range" min={1} max={6} step={0.5} value={inflation} onChange={(e) => setInflation(+e.target.value)} className="w-full" /></div>
      </div>

      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={showReal} onChange={(e) => setShowReal(e.target.checked)} /> Show inflation-adjusted (real) values</label>

      {chartData.length > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">{years}-Year Projection ({showReal ? "Real" : "Nominal"})</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}><XAxis dataKey="year" /><YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} /><Tooltip formatter={(v: number) => formatCurrency(v)} /><Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} /></LineChart>
          </ResponsiveContainer>
          <p className="text-xs text-muted-foreground mt-2">Line shows expected growth at 7% mean return. Percentiles below are from 1,000 stochastic simulations.</p>
        </div>
      )}

      {data && (
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(data.percentiles).map(([pct, val]) => {
            const adjusted = showReal ? val / Math.pow(1 + inflation / 100, years) : val;
            return <div key={pct} className="bg-card p-3 rounded-lg border border-border text-center"><p className="text-xs text-muted-foreground">{pct}th</p><p className="font-bold">{formatCurrency(adjusted)}</p></div>;
          })}
        </div>
      )}
    </div>
  );
}
