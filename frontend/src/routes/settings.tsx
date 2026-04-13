import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useRef } from "react";
import { api } from "@/api/client";
import { FileImport } from "@/components/file-import";
import { useToast } from "@/components/toast-provider";
import { MetricSkeleton, TableSkeleton } from "@/components/skeleton";
import { formatCurrency } from "@/lib/utils";
import { US_STATES, FILING_STATUSES, RISK_LABELS, ACCOUNT_TYPES } from "@/lib/constants";
import { Pencil, Trash2, Check, X as XIcon } from "lucide-react";
import type { DbStats, Account } from "@/types";

export const Route = createFileRoute("/settings")({ component: Settings });

const TABS = ["Profile", "Data", "Accounts", "Goals & Debts", "Security", "Config", "Storage", "Backup & Export"] as const;

function Settings() {
  const [tab, setTab] = useState<typeof TABS[number]>("Profile");
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="flex flex-wrap border-b border-border">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-3 py-2 text-sm -mb-px border-b-2 transition-colors ${tab === t ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"}`}>{t}</button>
        ))}
      </div>
      {tab === "Profile" && <ProfileTab />}
      {tab === "Data" && <DataTab />}
      {tab === "Config" && <ConfigTab />}
      {tab === "Backup & Export" && <ExportTab />}
      {tab === "Security" && <SecurityTab />}
      {tab === "Accounts" && <AccountsTab />}
      {tab === "Goals & Debts" && <p className="text-muted-foreground">Manage goals and debts on their dedicated pages.</p>}
      {tab === "Storage" && <StorageTab />}
    </div>
  );
}

// ── Profile with typed controls ─────────────────────────────────

function ProfileTab() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const { data, isLoading } = useQuery({ queryKey: ["settings", "profile"], queryFn: () => api.get<Record<string, unknown>>("/api/settings/profile") });
  const [form, setForm] = useState<Record<string, unknown>>({});
  const save = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.patch("/api/settings/profile", body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["settings"] }); toast.success("Profile saved"); },
    onError: (e) => toast.error(e.message),
  });

  if (isLoading) return <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <MetricSkeleton key={i} />)}</div>;
  if (!data) return null;
  const m = { ...data, ...form };

  const filled = [m.age, m.state_of_residence, m.risk_tolerance, m.retirement_target_age, m.filing_status, m.employer_match_pct].filter((v) => v != null && v !== "").length;
  const total = 6;
  const pct = Math.round((filled / total) * 100);

  return (
    <div className="max-w-lg space-y-5">
      <div>
        <div className="flex justify-between text-sm mb-1"><span className="font-medium">Profile Completeness</span><span>{pct}%</span></div>
        <div className="w-full bg-secondary rounded-full h-2"><div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${pct}%` }} /></div>
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">Age</label>
        <input type="number" min={18} max={100} value={Number(m.age) || ""} onChange={(e) => setForm({ ...form, age: +e.target.value })} className="w-full border rounded-md px-3 py-2" />
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">State of Residence</label>
        <select value={String(m.state_of_residence || "")} onChange={(e) => setForm({ ...form, state_of_residence: e.target.value })} className="w-full border rounded-md px-3 py-2">
          <option value="">Select state...</option>
          {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        {!m.state_of_residence && <p className="text-xs text-yellow-600 mt-1">Needed for state tax calculations and muni bond TEY</p>}
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">Risk Tolerance: {Number(m.risk_tolerance) || 5}/10</label>
        <input type="range" min={1} max={10} value={Number(m.risk_tolerance) || 5} onChange={(e) => setForm({ ...form, risk_tolerance: +e.target.value })} className="w-full" />
        <div className="flex justify-between text-xs text-muted-foreground"><span>Conservative</span><span>{RISK_LABELS[Number(m.risk_tolerance) || 5]}</span><span>Aggressive</span></div>
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">Retirement Target Age</label>
        <input type="number" min={50} max={90} value={Number(m.retirement_target_age) || ""} onChange={(e) => setForm({ ...form, retirement_target_age: +e.target.value })} className="w-full border rounded-md px-3 py-2" />
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">Filing Status</label>
        <select value={String(m.filing_status || "")} onChange={(e) => setForm({ ...form, filing_status: e.target.value })} className="w-full border rounded-md px-3 py-2">
          <option value="">Select...</option>
          {FILING_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">Employer 401k Match</label>
        <div className="flex items-center gap-2">
          <input type="number" min={0} max={100} step={0.5} value={Number(m.employer_match_pct) || ""} onChange={(e) => setForm({ ...form, employer_match_pct: +e.target.value })} className="flex-1 border rounded-md px-3 py-2" />
          <span className="text-muted-foreground">%</span>
        </div>
        {!m.employer_match_pct && <p className="text-xs text-yellow-600 mt-1">Needed for contribution priority strategy</p>}
      </div>

      <button onClick={() => save.mutate(form)} disabled={save.isPending} className="bg-primary text-primary-foreground px-6 py-2 rounded-md disabled:opacity-50">
        {save.isPending ? "Saving..." : "Save Profile"}
      </button>
    </div>
  );
}

// ── Data Management with granular clearing ───────────────────────

const CLEAR_GROUPS = [
  { label: "Financial Data", items: [{ key: "transactions", statsKey: "transactions", label: "Transactions" }, { key: "accounts", statsKey: "accounts", label: "Accounts" }, { key: "holdings", statsKey: "holdings", label: "Holdings" }, { key: "snapshots", statsKey: "snapshots", label: "Snapshots" }] },
  { label: "Tax", items: [{ key: "tax", statsKey: "tax_documents", label: "Tax Documents" }] },
  { label: "Planning", items: [{ key: "budgets", statsKey: "budgets", label: "Budgets" }, { key: "goals", statsKey: "goals", label: "Goals" }, { key: "debts", statsKey: "debts", label: "Debts" }] },
  { label: "AI & Chat", items: [{ key: "chats", statsKey: "chat_sessions", label: "Chat Sessions" }, { key: "prompts", statsKey: "prompts", label: "Custom Prompts" }] },
  { label: "System", items: [{ key: "category_rules", statsKey: "category_rules", label: "Category Rules" }, { key: "audit", statsKey: "audit_entries", label: "Audit Log" }] },
];

function DataTab() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const { data: stats, isLoading } = useQuery<DbStats>({ queryKey: ["settings", "stats"], queryFn: () => api.get("/api/settings/stats") });
  const clear = useMutation({
    mutationFn: (targets: string[]) => api.post("/api/settings/clear", { targets }),
    onSuccess: (_, targets) => { qc.invalidateQueries(); toast.success(`Cleared: ${targets.join(", ")}`); },
  });

  if (isLoading) return <div className="grid grid-cols-3 gap-3">{Array.from({ length: 9 }).map((_, i) => <MetricSkeleton key={i} />)}</div>;
  if (!stats) return null;

  const counts: Record<string, number> = stats as unknown as Record<string, number>;

  return (
    <div className="space-y-6">
      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">Import Financial Statement</h3>
        <FileImport type="statement" />
      </div>

      <h3 className="font-semibold">Database Statistics</h3>
      <div className="grid grid-cols-3 gap-3">{Object.entries(stats).map(([k, v]) => (
        <div key={k} className="bg-card p-3 rounded-lg border border-border"><p className="text-xs text-muted-foreground">{k}</p><p className="text-lg font-bold">{v}</p></div>
      ))}</div>

      <h3 className="font-semibold">Clear Data</h3>
      {CLEAR_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">{group.label}</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {group.items.map((item) => {
              const count = counts[item.statsKey];
              return (
                <button key={item.key} onClick={() => { if (confirm(`Delete all ${item.label.toLowerCase()}?`)) clear.mutate([item.key]); }}
                  disabled={count === 0}
                  className="px-3 py-1.5 text-sm border border-destructive text-destructive rounded-md hover:bg-destructive hover:text-white disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-1.5">
                  Clear {item.label}
                  <span className="bg-destructive/10 text-destructive px-1.5 py-0.5 rounded text-xs font-bold">{count ?? 0}</span>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      <div className="pt-2 border-t border-border">
        <button onClick={() => { if (confirm("Delete ALL data? This will create a backup first.") && confirm("Are you absolutely sure?")) clear.mutate(["all"]); }}
          className="px-4 py-2 text-sm bg-destructive text-white rounded-md font-medium">
          Clear ALL Data
        </button>
      </div>
    </div>
  );
}

// ── Config with slider values + diff badges ──────────────────────

function ConfigTab() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: () => api.get<Record<string, Record<string, { value: unknown; default: unknown; type: string; description: string; min?: number; max?: number; step?: number; options?: string[] }>>>("/api/config") });
  const update = useMutation({
    mutationFn: (body: { section: string; key: string; value: unknown }) => api.patch("/api/config", body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["config"] }); toast.success("Setting updated"); },
  });
  const reset = useMutation({
    mutationFn: (section?: string) => api.delete(`/api/config${section ? `?section=${section}` : ""}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["config"] }); toast.success("Reset to defaults"); },
  });

  if (!config) return <TableSkeleton />;

  let modifiedCount = 0;
  for (const fields of Object.values(config)) {
    for (const meta of Object.values(fields)) {
      if (String(meta.value) !== String(meta.default)) modifiedCount++;
    }
  }

  return (
    <div className="space-y-6">
      {modifiedCount > 0 && (
        <div className="flex items-center justify-between bg-yellow-50 border border-yellow-200 rounded-md px-4 py-2">
          <span className="text-sm text-yellow-800">{modifiedCount} setting{modifiedCount > 1 ? "s" : ""} modified from defaults</span>
          <button onClick={() => reset.mutate()} className="text-xs text-yellow-800 font-medium underline">Reset All</button>
        </div>
      )}
      {Object.entries(config).map(([section, fields]) => (
        <div key={section} className="bg-card p-4 rounded-lg border border-border">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold capitalize">{section}</h3>
            <button onClick={() => reset.mutate(section)} className="text-xs text-muted-foreground hover:text-primary">Reset section</button>
          </div>
          <div className="space-y-4">
            {Object.entries(fields).map(([key, meta]) => {
              const isModified = String(meta.value) !== String(meta.default);
              return (
                <div key={key} className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <label className="text-sm font-medium">{meta.description}</label>
                      {isModified && <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">Modified</span>}
                    </div>
                    <p className="text-xs text-muted-foreground">{key}</p>
                  </div>
                  <div className="w-52 flex items-center gap-2">
                    {meta.type === "toggle" ? (
                      <button onClick={() => update.mutate({ section, key, value: !meta.value })} className={`px-3 py-1 rounded text-sm ${meta.value ? "bg-primary text-white" : "bg-secondary"}`}>{meta.value ? "On" : "Off"}</button>
                    ) : meta.type === "select" && meta.options ? (
                      <select value={String(meta.value)} onChange={(e) => update.mutate({ section, key, value: e.target.value })} className="w-full border border-input rounded-md px-3 py-1.5 text-sm bg-background">{meta.options.map((o) => <option key={o}>{o}</option>)}</select>
                    ) : meta.type === "slider" ? (
                      <div className="w-full">
                        <input type="range" min={meta.min} max={meta.max} step={meta.step || 1} value={Number(meta.value)} onChange={(e) => update.mutate({ section, key, value: +e.target.value })} className="w-full" />
                        <span className="text-xs text-muted-foreground">{String(meta.value)}{meta.description?.includes("%") || meta.description?.includes("percent") ? "%" : ""}</span>
                      </div>
                    ) : (
                      <input value={String(meta.value)} onBlur={(e) => update.mutate({ section, key, value: e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Security with PIN strength ──────────────────────────────────

function SecurityTab() {
  const { toast } = useToast();
  const [pin, setPin] = useState("");
  const [current, setCurrent] = useState("");
  const manage = useMutation({
    mutationFn: (body: { pin: string; current_pin?: string }) => api.post("/api/settings/pin", body),
    onSuccess: () => toast.success(pin ? "PIN set" : "PIN removed"),
    onError: (e) => toast.error(e.message),
  });

  const strength = pin.length === 0 ? 0 : pin.length < 4 ? 1 : pin.length < 8 ? 2 : 3;
  const strengthLabel = ["", "Weak", "Good", "Strong"][strength];
  const strengthColor = ["", "bg-red-500", "bg-yellow-500", "bg-green-500"][strength];

  return (
    <div className="max-w-md space-y-5">
      <h3 className="font-semibold">PIN Authentication</h3>

      <div>
        <label className="text-sm font-medium block mb-1">Current PIN</label>
        <input type="password" placeholder="Required when changing an existing PIN" value={current} onChange={(e) => setCurrent(e.target.value)} className="w-full border rounded-md px-3 py-2" />
      </div>

      <div>
        <label className="text-sm font-medium block mb-1">New PIN</label>
        <input type="password" placeholder="4+ characters (leave empty to remove)" value={pin} onChange={(e) => setPin(e.target.value)} className="w-full border rounded-md px-3 py-2" />
        {pin.length > 0 && (
          <div className="mt-2">
            <div className="flex gap-1">{[1, 2, 3].map((i) => <div key={i} className={`h-1.5 flex-1 rounded ${i <= strength ? strengthColor : "bg-secondary"}`} />)}</div>
            <p className="text-xs text-muted-foreground mt-1">{strengthLabel}{pin.length < 4 ? " — must be at least 4 characters" : ""}</p>
          </div>
        )}
      </div>

      <button onClick={() => manage.mutate({ pin, current_pin: current || undefined })} disabled={manage.isPending || (pin.length > 0 && pin.length < 4)}
        className="bg-primary text-primary-foreground px-6 py-2 rounded-md disabled:opacity-50">
        {pin ? "Set PIN" : "Remove PIN"}
      </button>
    </div>
  );
}

// ── Storage ──────────────────────────────────────────────────────

function StorageTab() {
  const { data: backups } = useQuery({ queryKey: ["backups"], queryFn: () => api.get<Array<{ name: string; size: number; modified: string }>>("/api/backup/list") });
  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Backups</h3>
      {backups && backups.length > 0 ? (
        <div className="bg-card rounded-lg border border-border overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">File</th><th className="text-right px-4 py-2.5 font-medium">Size</th><th className="text-right px-4 py-2.5 font-medium">Date</th></tr></thead>
            <tbody>{backups.map((b) => <tr key={b.name} className="border-b border-border hover:bg-accent/30"><td className="px-4 py-2.5 font-mono text-xs">{b.name}</td><td className="px-4 py-2.5 text-right tabular-nums">{(b.size / 1024 / 1024).toFixed(1)} MB</td><td className="px-4 py-2.5 text-right text-muted-foreground">{b.modified}</td></tr>)}</tbody>
          </table>
        </div>
      ) : <p className="text-muted-foreground">No backups yet.</p>}
    </div>
  );
}

// ── Backup & Export ──────────────────────────────────────────────

function ExportTab() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const fileRef = useRef<HTMLInputElement>(null);
  const backup = useMutation({ mutationFn: () => api.post("/api/backup"), onSuccess: () => toast.success("Backup created") });
  const restoreMut = useMutation({ mutationFn: (file: File) => api.upload("/api/backup/restore", file), onSuccess: () => { qc.invalidateQueries(); toast.success("Database restored"); } });

  return (
    <div className="space-y-5">
      <h3 className="font-semibold">Backup</h3>
      <button onClick={() => backup.mutate()} className="bg-primary text-primary-foreground px-4 py-2 rounded-md">Create Backup</button>

      <h3 className="font-semibold">Restore from Backup</h3>
      <input ref={fileRef} type="file" accept=".db" className="text-sm" onChange={(e) => { if (e.target.files?.[0]) restoreMut.mutate(e.target.files[0]); }} />
      {restoreMut.isPending && <p className="text-sm text-muted-foreground">Restoring...</p>}

      <h3 className="font-semibold">Export Data</h3>
      <div className="flex flex-wrap gap-2">
        <a href="/api/export/transactions" className="px-3 py-2 text-sm border rounded-md hover:bg-accent">Transactions CSV</a>
        <a href="/api/export/holdings" className="px-3 py-2 text-sm border rounded-md hover:bg-accent">Holdings CSV</a>
        <a href="/api/export/tax" className="px-3 py-2 text-sm border rounded-md hover:bg-accent">Tax Data CSV</a>
        <a href="/api/export/report" className="px-3 py-2 text-sm border rounded-md hover:bg-accent">Report</a>
      </div>
    </div>
  );
}

// ── Accounts ─────────────────────────────────────────────────────

function AccountsTab() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const { data: accounts, isLoading } = useQuery<Account[]>({ queryKey: ["accounts"], queryFn: () => api.get("/api/accounts") });
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", institution: "", account_type: "checking" });

  const editMut = useMutation({
    mutationFn: ({ id, body }: { id: number; body: typeof form }) => api.patch(`/api/accounts/${id}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["accounts"] }); setEditing(null); toast.success("Account updated"); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => api.delete(`/api/accounts/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["accounts"] }); toast.success("Account deleted"); },
  });

  if (isLoading) return <TableSkeleton />;
  if (!accounts || accounts.length === 0) return <p className="text-muted-foreground">No accounts. Import a statement to create one.</p>;

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Accounts</h3>
      <div className="bg-card rounded-lg border border-border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted">
              <th className="text-left px-4 py-2.5 font-medium">Institution</th>
              <th className="text-left px-4 py-2.5 font-medium">Name</th>
              <th className="text-left px-4 py-2.5 font-medium">Type</th>
              <th className="text-right px-4 py-2.5 font-medium">Transactions</th>
              <th className="text-right px-4 py-2.5 font-medium">Last Activity</th>
              <th className="w-20 px-4 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id} className="border-b border-border hover:bg-accent/30">
                {editing === a.id ? (
                  <>
                    <td className="px-4 py-2.5">
                      <input value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} className="w-full border border-input rounded-md px-2 py-1 text-sm bg-background" />
                    </td>
                    <td className="px-4 py-2.5">
                      <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-input rounded-md px-2 py-1 text-sm bg-background" />
                    </td>
                    <td className="px-4 py-2.5">
                      <select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })} className="border border-input rounded-md px-2 py-1 text-sm bg-background">
                        {ACCOUNT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2.5" />
                    <td className="px-4 py-2.5" />
                    <td className="px-4 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => editMut.mutate({ id: a.id, body: form })} title="Save" className="p-1.5 hover:bg-accent active:bg-accent rounded-md text-primary"><Check size={15} /></button>
                        <button onClick={() => setEditing(null)} title="Cancel" className="p-1.5 hover:bg-accent active:bg-accent rounded-md text-muted-foreground"><XIcon size={15} /></button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-2.5 font-medium">{a.institution}</td>
                    <td className="px-4 py-2.5">{a.name}</td>
                    <td className="px-4 py-2.5"><span className="text-xs bg-secondary px-2 py-0.5 rounded-full">{a.account_type}</span></td>
                    <td className="px-4 py-2.5 text-right tabular-nums">{a.transaction_count.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-right text-muted-foreground">{a.last_activity || "—"}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => { setEditing(a.id); setForm({ name: a.name, institution: a.institution, account_type: a.account_type }); }} title="Edit" className="p-1.5 hover:bg-accent active:bg-accent rounded-md text-muted-foreground hover:text-primary active:text-primary transition-colors"><Pencil size={15} /></button>
                        <button onClick={() => { if (confirm(`Delete ${a.name} and all its data?`)) deleteMut.mutate(a.id); }} title="Delete" className="p-1.5 hover:bg-red-100 active:bg-red-100 rounded-md text-muted-foreground hover:text-destructive active:text-destructive transition-colors"><Trash2 size={15} /></button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
