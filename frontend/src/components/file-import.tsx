import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

interface ImportResult {
  status: string;
  transactions_added?: number;
  holdings_added?: number;
  duplicates_skipped?: number;
  transfers_linked?: number;
  warnings?: string[];
  id?: number;
  doc_type?: string;
  tax_year?: number;
  fields?: number;
  confidence?: number;
}

interface FileImportProps {
  type: "statement" | "tax";
  onSuccess?: () => void;
  compact?: boolean;
}

export function FileImport({ type, onSuccess, compact = false }: FileImportProps) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const endpoint = type === "tax" ? "/api/tax/upload" : "/api/import/statement";
  const accept = type === "tax" ? ".pdf" : ".pdf,.csv,.tsv,.ofx,.qfx";
  const label = type === "tax" ? "Tax Document (PDF)" : "Statement (PDF, CSV, OFX/QFX)";

  const mutation = useMutation<ImportResult, Error, File>({
    mutationFn: (file) => api.upload(endpoint, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["expenses"] });
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["investments"] });
      qc.invalidateQueries({ queryKey: ["tax"] });
      qc.invalidateQueries({ queryKey: ["import"] });
      qc.invalidateQueries({ queryKey: ["settings"] });
      onSuccess?.();
    },
  });

  const handleFile = (file: File | undefined) => {
    if (file) mutation.mutate(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <input ref={fileRef} type="file" accept={accept} className="hidden" onChange={(e) => handleFile(e.target.files?.[0])} />
        <button onClick={() => fileRef.current?.click()} disabled={mutation.isPending} className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50">
          {mutation.isPending ? "Importing..." : `Import ${type === "tax" ? "Tax Doc" : "Statement"}`}
        </button>
        {mutation.isSuccess && <span className="text-xs text-green-600">Done</span>}
        {mutation.isError && <span className="text-xs text-destructive">{mutation.error.message}</span>}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
      >
        <input ref={fileRef} type="file" accept={accept} className="hidden" onChange={(e) => handleFile(e.target.files?.[0])} />
        <p className="text-sm font-medium">{mutation.isPending ? "Importing..." : `Drop ${label} here or click to browse`}</p>
        <p className="text-xs text-muted-foreground mt-1">{accept.replace(/\./g, "").toUpperCase().replace(/,/g, ", ")}</p>
      </div>

      {mutation.isSuccess && mutation.data && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm space-y-1">
          <p className="font-medium text-green-800">Import successful</p>
          {mutation.data.transactions_added !== undefined && <p>Transactions added: {mutation.data.transactions_added}</p>}
          {mutation.data.holdings_added !== undefined && mutation.data.holdings_added > 0 && <p>Holdings added: {mutation.data.holdings_added}</p>}
          {mutation.data.duplicates_skipped !== undefined && mutation.data.duplicates_skipped > 0 && <p>Duplicates skipped: {mutation.data.duplicates_skipped}</p>}
          {mutation.data.doc_type && <p>Document type: {mutation.data.doc_type}</p>}
          {mutation.data.tax_year && <p>Tax year: {mutation.data.tax_year}</p>}
          {mutation.data.warnings && mutation.data.warnings.length > 0 && (
            <div className="mt-2">{mutation.data.warnings.map((w, i) => <p key={i} className="text-yellow-700 text-xs">{w}</p>)}</div>
          )}
        </div>
      )}

      {mutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-800">
          {mutation.error.message}
        </div>
      )}
    </div>
  );
}
