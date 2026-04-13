import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { formatCurrency } from "@/lib/utils";

interface ArtifactFile {
  filename: string;
  type: string;
  size: number;
  modified: string;
}

interface ArtifactStats {
  count: number;
  total_size: number;
  oldest: string | null;
  newest: string | null;
}

interface StatementPreview {
  preview_type: "statement";
  institution: string | null;
  transaction_count: number;
  holding_count: number;
  date_range: [string, string] | null;
  total_debits: number;
  total_credits: number;
  transactions: Array<{ date: string; amount: number; description: string }>;
  warnings: string[];
}

interface TaxPreview {
  preview_type: "tax";
  doc_type: string;
  tax_year: number | null;
  confidence: number;
  fields: Record<string, string>;
  warnings: string[];
}

type Preview = StatementPreview | TaxPreview;

const TYPE_COLORS: Record<string, string> = {
  pdf: "bg-red-100 text-red-800",
  csv: "bg-green-100 text-green-800",
  ofx: "bg-blue-100 text-blue-800",
  qfx: "bg-blue-100 text-blue-800",
  tsv: "bg-green-100 text-green-800",
  other: "bg-gray-100 text-gray-800",
};

export const Route = createFileRoute("/artifacts")({ component: Artifacts });

function Artifacts() {
  const qc = useQueryClient();
  const [previewFile, setPreviewFile] = useState<string | null>(null);

  const { data: files } = useQuery<ArtifactFile[]>({ queryKey: ["artifacts"], queryFn: () => api.get("/api/artifacts") });
  const { data: stats } = useQuery<ArtifactStats>({ queryKey: ["artifacts", "stats"], queryFn: () => api.get("/api/artifacts/stats") });
  const { data: preview, isLoading: previewLoading } = useQuery<Preview>({
    queryKey: ["artifacts", "preview", previewFile],
    queryFn: () => api.get(`/api/artifacts/${previewFile}/preview`),
    enabled: !!previewFile,
  });

  const deleteMut = useMutation({
    mutationFn: (filename: string) => api.delete(`/api/artifacts/${filename}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["artifacts"] }); setPreviewFile(null); },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Imported Files</h1>

      {/* Stats header */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-card p-3 rounded-lg border border-border">
            <p className="text-sm text-muted-foreground">Files</p>
            <p className="text-xl font-bold">{stats.count}</p>
          </div>
          <div className="bg-card p-3 rounded-lg border border-border">
            <p className="text-sm text-muted-foreground">Total Size</p>
            <p className="text-xl font-bold">{formatSize(stats.total_size)}</p>
          </div>
          <div className="bg-card p-3 rounded-lg border border-border">
            <p className="text-sm text-muted-foreground">Oldest</p>
            <p className="text-sm font-medium">{stats.oldest || "—"}</p>
          </div>
          <div className="bg-card p-3 rounded-lg border border-border">
            <p className="text-sm text-muted-foreground">Newest</p>
            <p className="text-sm font-medium">{stats.newest || "—"}</p>
          </div>
        </div>
      )}

      {/* File table */}
      {files && files.length > 0 ? (
        <div className="bg-card rounded-lg border border-border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted">
                <th className="text-left px-4 py-2.5 font-medium">Filename</th>
                <th className="text-left px-4 py-2.5 font-medium">Type</th>
                <th className="text-right px-4 py-2.5 font-medium">Size</th>
                <th className="text-left px-4 py-2.5 font-medium">Imported</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.filename} className={`border-b border-border hover:bg-accent/30 ${previewFile === f.filename ? "bg-accent/50" : ""}`}>
                  <td className="px-4 py-2.5 font-mono text-xs truncate max-w-xs" title={f.filename}>{f.filename}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium uppercase ${TYPE_COLORS[f.type] || TYPE_COLORS.other}`}>{f.type}</span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">{formatSize(f.size)}</td>
                  <td className="px-4 py-2.5 text-muted-foreground">{f.modified}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => setPreviewFile(previewFile === f.filename ? null : f.filename)} className="text-xs text-primary hover:underline">
                        {previewFile === f.filename ? "Hide" : "Preview"}
                      </button>
                      <a href={`/api/artifacts/${f.filename}`} className="text-xs text-primary hover:underline">Download</a>
                      <button onClick={() => { if (confirm(`Delete ${f.filename}?`)) deleteMut.mutate(f.filename); }} className="text-xs text-destructive hover:underline">Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-card p-8 rounded-lg border border-border text-center text-muted-foreground">
          No imported files stored yet. Files will appear here after importing statements or tax documents.
        </div>
      )}

      {/* Preview panel */}
      {previewFile && (
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-semibold mb-3">Preview: {previewFile}</h3>
          {previewLoading ? (
            <p className="text-muted-foreground animate-pulse">Parsing file...</p>
          ) : preview ? (
            preview.preview_type === "tax" ? <TaxPreviewPanel data={preview} /> : <StatementPreviewPanel data={preview} />
          ) : (
            <p className="text-muted-foreground">Unable to preview this file.</p>
          )}
        </div>
      )}
    </div>
  );
}

function StatementPreviewPanel({ data }: { data: StatementPreview }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-4 gap-3 text-sm">
        <div><span className="text-muted-foreground">Institution:</span> {data.institution || "Unknown"}</div>
        <div><span className="text-muted-foreground">Transactions:</span> {data.transaction_count}</div>
        <div><span className="text-muted-foreground">Holdings:</span> {data.holding_count}</div>
        <div><span className="text-muted-foreground">Date range:</span> {data.date_range ? `${data.date_range[0]} to ${data.date_range[1]}` : "—"}</div>
      </div>
      <div className="text-sm">
        <span className="text-red-600">Debits: {formatCurrency(Math.abs(data.total_debits))}</span>
        {" | "}
        <span className="text-green-600">Credits: {formatCurrency(data.total_credits)}</span>
      </div>
      {data.warnings.length > 0 && (
        <div className="text-xs text-yellow-700">{data.warnings.map((w, i) => <p key={i}>{w}</p>)}</div>
      )}
      {data.transactions.length > 0 && (
        <div className="rounded-lg border border-border overflow-x-auto mt-2">
          <table className="w-full text-xs">
            <thead><tr className="border-b bg-muted"><th className="text-left px-3 py-2 font-medium">Date</th><th className="text-right px-3 py-2 font-medium">Amount</th><th className="text-left px-3 py-2 font-medium">Description</th></tr></thead>
            <tbody>{data.transactions.map((t, i) => (
              <tr key={i} className="border-b border-border hover:bg-accent/30">
                <td className="px-3 py-1.5">{t.date}</td>
                <td className={`px-3 py-1.5 text-right tabular-nums ${t.amount < 0 ? "text-red-600" : "text-green-600"}`}>{formatCurrency(t.amount)}</td>
                <td className="px-3 py-1.5 truncate max-w-xs">{t.description}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {data.transaction_count > 20 && <p className="text-xs text-muted-foreground">Showing first 20 of {data.transaction_count} transactions.</p>}
    </div>
  );
}

function TaxPreviewPanel({ data }: { data: TaxPreview }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div><span className="text-muted-foreground">Form Type:</span> <span className="font-medium">{data.doc_type}</span></div>
        <div><span className="text-muted-foreground">Tax Year:</span> {data.tax_year || "Unknown"}</div>
        <div><span className="text-muted-foreground">Confidence:</span> {(data.confidence * 100).toFixed(0)}%</div>
      </div>
      {data.warnings.length > 0 && (
        <div className="text-xs text-yellow-700">{data.warnings.map((w, i) => <p key={i}>{w}</p>)}</div>
      )}
      {Object.keys(data.fields).length > 0 && (
        <div className="space-y-1">
          <h4 className="font-medium text-sm">Extracted Fields</h4>
          {Object.entries(data.fields).map(([key, val]) => (
            <div key={key} className="flex gap-2 text-sm">
              <span className="text-muted-foreground font-mono text-xs w-24">{key}</span>
              <span>{val}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
