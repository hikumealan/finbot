import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";
import type { Goal } from "@/types";

export const Route = createFileRoute("/goals")({ component: Goals });

function Goals() {
  const qc = useQueryClient();
  const { data: goals } = useQuery<Goal[]>({ queryKey: ["goals"], queryFn: () => api.get("/api/goals") });
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", goal_type: "retirement", target_amount: 0, current_amount: 0, target_date: "" });

  const invalidate = () => { qc.invalidateQueries({ queryKey: ["goals"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); };
  const addMut = useMutation({ mutationFn: (b: typeof form) => api.post("/api/goals", { ...b, target_date: b.target_date || null }), onSuccess: () => { invalidate(); setAdding(false); setForm({ name: "", goal_type: "retirement", target_amount: 0, current_amount: 0, target_date: "" }); } });
  const editMut = useMutation({ mutationFn: ({ id, body }: { id: number; body: typeof form }) => api.patch(`/api/goals/${id}`, { ...body, target_date: body.target_date || null }), onSuccess: () => { invalidate(); setEditing(null); } });
  const deleteMut = useMutation({ mutationFn: (id: number) => api.delete(`/api/goals/${id}`), onSuccess: invalidate });

  const startEdit = (g: Goal) => { setEditing(g.id); setForm({ name: g.name, goal_type: g.goal_type, target_amount: g.target_amount, current_amount: g.current_amount, target_date: g.target_date || "" }); };

  if (!goals) return <div>Loading...</div>;

  const statusColors: Record<string, string> = { on_track: "bg-green-100 text-green-800", ahead: "bg-blue-100 text-blue-800", behind: "bg-yellow-100 text-yellow-800", complete: "bg-purple-100 text-purple-800" };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Financial Goals</h1>
        <button onClick={() => setAdding(!adding)} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md">{adding ? "Cancel" : "+ Add Goal"}</button>
      </div>

      {adding && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-medium mb-3">Add Goal</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="border rounded px-2 py-1" />
            <select value={form.goal_type} onChange={(e) => setForm({ ...form, goal_type: e.target.value })} className="border border-input rounded-md px-3 py-2 text-sm bg-background">{["retirement", "emergency_fund", "house", "college", "custom"].map((t) => <option key={t} value={t}>{t}</option>)}</select>
            <input type="number" placeholder="Target ($)" value={form.target_amount || ""} onChange={(e) => setForm({ ...form, target_amount: +e.target.value })} className="border rounded px-2 py-1" />
            <input type="number" placeholder="Current ($)" value={form.current_amount || ""} onChange={(e) => setForm({ ...form, current_amount: +e.target.value })} className="border rounded px-2 py-1" />
            <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} className="border rounded px-2 py-1" />
          </div>
          <button onClick={() => { if (form.name) addMut.mutate(form); }} className="mt-3 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm">Save</button>
        </div>
      )}

      {goals.length === 0 ? <p className="text-muted-foreground">No goals set. Click "+ Add Goal" to get started.</p> : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {goals.map((g) => (
            <div key={g.id} className="bg-card p-4 rounded-lg border border-border">
              {editing === g.id ? (
                <div className="space-y-2">
                  <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="border rounded px-2 py-1 w-full" />
                  <div className="grid grid-cols-2 gap-2">
                    <input type="number" value={form.target_amount} onChange={(e) => setForm({ ...form, target_amount: +e.target.value })} className="border rounded px-2 py-1" placeholder="Target" />
                    <input type="number" value={form.current_amount} onChange={(e) => setForm({ ...form, current_amount: +e.target.value })} className="border rounded px-2 py-1" placeholder="Current" />
                  </div>
                  <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} className="border rounded px-2 py-1 w-full" />
                  <div className="flex gap-2">
                    <button onClick={() => editMut.mutate({ id: g.id, body: form })} className="text-sm text-primary font-medium">Save</button>
                    <button onClick={() => setEditing(null)} className="text-sm text-muted-foreground">Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex justify-between items-start mb-2">
                    <div><h3 className="font-semibold">{g.name}</h3><p className="text-xs text-muted-foreground">{g.goal_type}</p></div>
                    <div className="flex gap-2 items-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${statusColors[g.status] || "bg-gray-100"}`}>{g.status.toUpperCase()}</span>
                      <button onClick={() => startEdit(g)} className="text-xs text-muted-foreground hover:text-primary active:text-primary">Edit</button>
                      <button onClick={() => deleteMut.mutate(g.id)} className="text-xs text-destructive hover:text-red-700 active:text-red-700">Del</button>
                    </div>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-3 mb-2"><div className="h-3 rounded-full bg-primary transition-all" style={{ width: `${Math.min(g.progress_pct, 100)}%` }} /></div>
                  <div className="flex justify-between text-sm"><span>{formatCurrency(g.current_amount)}</span><span>{formatCurrency(g.target_amount)}</span></div>
                  {g.monthly_needed > 0 && <p className="text-xs text-muted-foreground mt-1">Need {formatCurrency(g.monthly_needed)}/month</p>}
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
