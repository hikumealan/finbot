import { useState, useEffect, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

const PAGES = [
  { label: "Dashboard", path: "/" },
  { label: "Expenses", path: "/expenses" },
  { label: "Investments", path: "/investments" },
  { label: "Muni Bonds", path: "/muni-bonds" },
  { label: "Debts", path: "/debts" },
  { label: "Goals", path: "/goals" },
  { label: "Projections", path: "/projections" },
  { label: "Tax Center", path: "/tax" },
  { label: "AI Advisor", path: "/advisor" },
  { label: "Settings", path: "/settings" },
  { label: "Database", path: "/db" },
  { label: "Files", path: "/artifacts" },
  { label: "User Guide", path: "/guide" },
];

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const { data: searchResults } = useQuery({
    queryKey: ["search", query],
    queryFn: () => api.get<Array<{ type: string; title: string; subtitle: string; path: string }>>(`/api/search?q=${encodeURIComponent(query)}`),
    enabled: open && query.length >= 2,
  });

  useEffect(() => { if (open) { setQuery(""); setTimeout(() => inputRef.current?.focus(), 50); } }, [open]);

  if (!open) return null;

  const filteredPages = PAGES.filter((p) => p.label.toLowerCase().includes(query.toLowerCase()));
  const allResults = [
    ...filteredPages.map((p) => ({ type: "page" as const, label: p.label, subtitle: p.path, path: p.path })),
    ...(searchResults || []).map((r) => ({ type: r.type, label: r.title, subtitle: r.subtitle, path: r.path })),
  ].slice(0, 15);

  const handleSelect = (path: string) => {
    navigate({ to: path });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-full max-w-lg bg-card rounded-xl shadow-2xl border border-border overflow-hidden">
        <input ref={inputRef} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search pages, transactions, accounts..."
          className="w-full px-4 py-3 border-b border-border bg-transparent outline-none text-sm" onKeyDown={(e) => { if (e.key === "Escape") onClose(); if (e.key === "Enter" && allResults[0]) handleSelect(allResults[0].path); }} />
        <div className="max-h-72 overflow-y-auto">
          {allResults.length === 0 && query.length >= 2 && <p className="p-4 text-sm text-muted-foreground">No results</p>}
          {allResults.map((r, i) => (
            <button key={`${r.type}-${i}`} onClick={() => handleSelect(r.path)} className="w-full text-left px-4 py-2 text-sm hover:bg-accent flex items-center gap-3">
              <span className="text-xs bg-secondary px-1.5 py-0.5 rounded uppercase">{r.type}</span>
              <span className="flex-1 truncate">{r.label}</span>
              <span className="text-xs text-muted-foreground">{r.subtitle}</span>
            </button>
          ))}
        </div>
        <div className="px-4 py-2 border-t border-border text-xs text-muted-foreground">
          <kbd className="bg-secondary px-1 rounded">Enter</kbd> select · <kbd className="bg-secondary px-1 rounded">Esc</kbd> close
        </div>
      </div>
    </div>
  );
}
