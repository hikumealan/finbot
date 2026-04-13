import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { FileImport } from "@/components/file-import";

export const Route = createFileRoute("/muni-bonds")({ component: MuniBonds });

function MuniBonds() {
  const qc = useQueryClient();
  const [showImport, setShowImport] = useState(false);
  const [coupon, setCoupon] = useState(3.5);
  const [fedRate, setFedRate] = useState(32);
  const [stateRate, setStateRate] = useState(5);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ issuer_state: "", coupon_rate: 0, credit_rating: "", is_amt_subject: false });

  const tey = useMutation({ mutationFn: () => api.post<{ tey: number; combined_rate: number }>("/api/munis/tey", { coupon: coupon / 100, federal_rate: fedRate / 100, state_rate: stateRate / 100, in_state: true }) });
  const { data: holdings } = useQuery({ queryKey: ["munis", "holdings"], queryFn: () => api.get<Array<{ symbol: string; coupon_rate: number; tey: number; is_in_state: boolean; credit_rating: string | null; is_amt_subject: boolean }>>("/api/munis/holdings") });

  const { data: rawHoldings } = useQuery({ queryKey: ["holdings"], queryFn: () => api.get<Array<{ id: number; symbol: string; asset_class: string }>>("/api/investments/holdings") });
  const muniHoldingIds = rawHoldings?.filter((h) => h.asset_class === "muni_bond") || [];

  const editMut = useMutation({
    mutationFn: ({ id, body }: { id: number; body: typeof editForm }) => api.patch(`/api/munis/${id}`, { ...body, coupon_rate: body.coupon_rate / 100 }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["munis"] }); qc.invalidateQueries({ queryKey: ["holdings"] }); setEditingId(null); },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Municipal Bonds</h1>
        <button onClick={() => setShowImport(!showImport)} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md">{showImport ? "Hide" : "Import Statement"}</button>
      </div>
      {showImport && <div className="bg-card p-4 rounded-lg border border-border"><FileImport type="statement" onSuccess={() => setShowImport(false)} /></div>}

      <div className="bg-card p-4 rounded-lg border border-border">
        <h3 className="font-semibold mb-3">TEY Calculator</h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div><label className="text-sm">Coupon (%)</label><input type="number" value={coupon} onChange={(e) => setCoupon(+e.target.value)} step={0.1} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm">Federal Rate (%)</label><input type="number" value={fedRate} onChange={(e) => setFedRate(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
          <div><label className="text-sm">State Rate (%)</label><input type="number" value={stateRate} onChange={(e) => setStateRate(+e.target.value)} className="w-full border rounded px-2 py-1" /></div>
        </div>
        <button onClick={() => tey.mutate()} className="bg-primary text-primary-foreground px-4 py-2 rounded-md">Calculate</button>
        {tey.data && <p className="mt-3 text-lg">TEY: <span className="font-bold text-primary">{(tey.data.tey * 100).toFixed(2)}%</span></p>}
      </div>

      {holdings && holdings.length > 0 && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Muni Holdings</h3>
          <div className="rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted"><th className="text-left px-4 py-2.5 font-medium">Symbol</th><th className="text-right px-4 py-2.5 font-medium">Coupon</th><th className="text-right px-4 py-2.5 font-medium">TEY</th><th className="text-left px-4 py-2.5 font-medium">In-State</th><th className="text-left px-4 py-2.5 font-medium">Rating</th><th className="text-left px-4 py-2.5 font-medium">AMT</th><th className="px-4 py-2.5"></th></tr></thead>
              <tbody>{holdings.map((h, i) => {
                const holdingRecord = muniHoldingIds.find((r) => r.symbol === h.symbol);
                return (
                  <tr key={h.symbol} className="border-b border-border hover:bg-accent/30">
                    <td className="px-4 py-2.5 font-mono">{h.symbol}</td><td className="px-4 py-2.5 text-right tabular-nums">{(h.coupon_rate * 100).toFixed(2)}%</td><td className="px-4 py-2.5 text-right tabular-nums font-bold">{(h.tey * 100).toFixed(2)}%</td>
                    <td className="px-4 py-2.5">{h.is_in_state ? "Yes" : ""}</td><td className="px-4 py-2.5">{h.credit_rating || "N/A"}</td><td className="px-4 py-2.5">{h.is_amt_subject ? "Yes" : ""}</td>
                    <td className="px-4 py-2.5"><div className="flex items-center justify-end">{holdingRecord && <button onClick={() => { setEditingId(holdingRecord.id); setEditForm({ issuer_state: "", coupon_rate: h.coupon_rate * 100, credit_rating: h.credit_rating || "", is_amt_subject: h.is_amt_subject }); }} className="text-xs text-primary hover:underline active:underline">Edit</button>}</div></td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
        </div>
      )}

      {editingId && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Edit Muni Details</h3>
          <div className="grid grid-cols-4 gap-3">
            <div><label className="text-sm">Issuer State</label><input value={editForm.issuer_state} onChange={(e) => setEditForm({ ...editForm, issuer_state: e.target.value })} maxLength={2} className="border rounded px-2 py-1 w-full" /></div>
            <div><label className="text-sm">Coupon (%)</label><input type="number" value={editForm.coupon_rate} onChange={(e) => setEditForm({ ...editForm, coupon_rate: +e.target.value })} step={0.1} className="border rounded px-2 py-1 w-full" /></div>
            <div><label className="text-sm">Credit Rating</label><input value={editForm.credit_rating} onChange={(e) => setEditForm({ ...editForm, credit_rating: e.target.value })} className="border rounded px-2 py-1 w-full" /></div>
            <div className="flex items-end gap-2"><label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={editForm.is_amt_subject} onChange={(e) => setEditForm({ ...editForm, is_amt_subject: e.target.checked })} /> AMT</label></div>
          </div>
          <div className="flex gap-2 mt-3">
            <button onClick={() => editMut.mutate({ id: editingId, body: editForm })} className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm">Save</button>
            <button onClick={() => setEditingId(null)} className="text-sm text-muted-foreground">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
