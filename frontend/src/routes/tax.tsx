import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { FileImport } from "@/components/file-import";
import { formatCurrency } from "@/lib/utils";
import type { TaxPosition } from "@/types";

export const Route = createFileRoute("/tax")({ component: TaxCenter });

function TaxCenter() {
  const qc = useQueryClient();
  const { data: pos } = useQuery<TaxPosition>({ queryKey: ["tax", "position"], queryFn: () => api.get("/api/tax/position") });
  const { data: tlh } = useQuery({ queryKey: ["tax", "tlh"], queryFn: () => api.get<Array<{ symbol: string; cost_basis: number; current_value: number; unrealized_loss: number; in_wash_window: boolean }>>("/api/tax/tlh") });
  const { data: docs } = useQuery({ queryKey: ["tax", "documents"], queryFn: () => api.get<Array<{ id: number; tax_year: number; doc_type: string; source_file: string }>>("/api/tax/documents") });

  const deleteMut = useMutation({ mutationFn: (id: number) => api.delete(`/api/tax/documents/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["tax"] }) });

  const [editingDoc, setEditingDoc] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Tax Center</h1>

      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">Import Tax Document</h3>
        <FileImport type="tax" />
      </div>

      {pos && pos.gross_income > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Tax Position</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><p className="text-sm text-muted-foreground">Gross Income</p><p className="font-bold">{formatCurrency(pos.gross_income)}</p></div>
            <div><p className="text-sm text-muted-foreground">Taxable Income</p><p className="font-bold">{formatCurrency(pos.taxable_income)}</p></div>
            <div><p className="text-sm text-muted-foreground">Effective Rate</p><p className="font-bold">{(pos.effective_rate * 100).toFixed(1)}%</p></div>
            <div><p className="text-sm text-muted-foreground">Marginal Rate</p><p className="font-bold">{(pos.combined_marginal_rate * 100).toFixed(1)}%</p></div>
          </div>
          <p className="text-sm mt-2">Federal: {(pos.federal_marginal_rate * 100).toFixed(1)}% | State: {(pos.state_rate * 100).toFixed(1)}% | Std Deduction: {formatCurrency(pos.standard_deduction)} | Total Tax: {formatCurrency(pos.total_tax)}</p>
        </div>
      )}

      {tlh && tlh.length > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Tax-Loss Harvesting Candidates</h3>
          <div className="rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Symbol</th><th className="text-right px-4 py-2.5 font-medium">Cost Basis</th><th className="text-right px-4 py-2.5 font-medium">Current</th><th className="text-right px-4 py-2.5 font-medium">Loss</th><th className="text-left px-4 py-2.5 font-medium">Wash</th></tr></thead>
              <tbody>{tlh.map((c) => <tr key={c.symbol} className="border-b border-border hover:bg-accent/30"><td className="px-4 py-2.5 font-mono">{c.symbol}</td><td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(c.cost_basis)}</td><td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(c.current_value)}</td><td className="px-4 py-2.5 text-right tabular-nums text-red-600">{formatCurrency(c.unrealized_loss)}</td><td className="px-4 py-2.5">{c.in_wash_window ? "Yes" : ""}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      )}

      {docs && docs.length > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Imported Documents</h3>
          <div className="rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Year</th><th className="text-left px-4 py-2.5 font-medium">Type</th><th className="text-left px-4 py-2.5 font-medium">File</th><th className="px-4 py-2.5"></th></tr></thead>
              <tbody>{docs.map((d) => (
                <tr key={d.id} className="border-b border-border hover:bg-accent/30">
                  <td className="px-4 py-2.5 tabular-nums">{d.tax_year}</td><td className="px-4 py-2.5">{d.doc_type}</td><td className="px-4 py-2.5 font-mono text-xs">{d.source_file}</td>
                  <td className="px-4 py-2.5"><div className="flex items-center justify-end gap-2"><button onClick={() => setEditingDoc(editingDoc === d.id ? null : d.id)} className="text-xs text-primary hover:underline active:underline">Edit Fields</button><button onClick={() => { if (confirm("Delete this document?")) deleteMut.mutate(d.id); }} className="text-xs text-destructive hover:text-red-700 active:text-red-700">Delete</button></div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>

          {editingDoc && <FieldEditor docId={editingDoc} />}
        </div>
      )}
    </div>
  );
}

function FieldEditor({ docId }: { docId: number }) {
  const qc = useQueryClient();
  const { data: fields } = useQuery({ queryKey: ["tax", "fields", docId], queryFn: () => api.get<Array<{ id: number; field_key: string; field_label: string; value: string }>>(`/api/tax/documents/${docId}/fields`) });
  const [editingField, setEditingField] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");

  const saveMut = useMutation({
    mutationFn: ({ fieldId, value }: { fieldId: number; value: string }) => api.patch(`/api/tax/documents/${docId}/fields/${fieldId}`, { value }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["tax"] }); setEditingField(null); },
  });

  if (!fields) return <div className="text-sm text-muted-foreground p-2">Loading fields...</div>;

  return (
    <div className="mt-3 bg-muted p-3 rounded-md">
      <h4 className="font-medium text-sm mb-2">Document Fields (click value to edit)</h4>
      <div className="space-y-1">
        {fields.map((f) => (
          <div key={f.id} className="flex items-center gap-2 text-sm">
            <span className="w-32 text-muted-foreground font-mono text-xs">{f.field_key}</span>
            <span className="w-40 text-muted-foreground">{f.field_label}</span>
            {editingField === f.id ? (
              <>
                <input value={editValue} onChange={(e) => setEditValue(e.target.value)} className="border rounded px-1 py-0.5 flex-1 text-xs" autoFocus />
                <button onClick={() => saveMut.mutate({ fieldId: f.id, value: editValue })} className="text-xs text-primary">Save</button>
                <button onClick={() => setEditingField(null)} className="text-xs text-muted-foreground">Cancel</button>
              </>
            ) : (
              <span onClick={() => { setEditingField(f.id); setEditValue(f.value); }} className="flex-1 cursor-pointer hover:bg-accent active:bg-accent px-1 py-0.5 rounded border-b border-dashed border-muted-foreground/30">{f.value}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
