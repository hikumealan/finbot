import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";

interface TableInfo {
  name: string;
  row_count: number;
  column_count: number;
}

interface TableData {
  table: string;
  columns: Array<{ name: string; type: string }>;
  rows: Array<Record<string, unknown>>;
  total: number;
  limit: number;
  offset: number;
}

export const Route = createFileRoute("/db")({ component: DbViewer });

function DbViewer() {
  const [selected, setSelected] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [search, setSearch] = useState("");

  const { data: tables } = useQuery<TableInfo[]>({
    queryKey: ["db", "tables"],
    queryFn: () => api.get("/api/db/tables"),
  });

  const searchParam = search.length >= 2 ? `&search=${encodeURIComponent(search)}` : "";
  const sortParam = sortBy ? `&sort_by=${sortBy}&sort_dir=${sortDir}` : "";

  const { data: tableData, isLoading } = useQuery<TableData>({
    queryKey: ["db", "table", selected, page, pageSize, sortBy, sortDir, search],
    queryFn: () => api.get(`/api/db/tables/${selected}?limit=${pageSize}&offset=${page * pageSize}${sortParam}${searchParam}`),
    enabled: !!selected,
  });

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortDir("asc");
    }
    setPage(0);
  };

  const totalPages = tableData ? Math.ceil(tableData.total / pageSize) : 0;

  return (
    <div className="flex gap-4 h-[calc(100vh-6rem)]">
      {/* Table selector sidebar */}
      <div className="w-52 border-r border-border pr-4 overflow-y-auto shrink-0">
        <h2 className="font-bold text-lg mb-3">Database</h2>
        <div className="space-y-0.5">
          {tables?.map((t) => (
            <button
              key={t.name}
              onClick={() => { setSelected(t.name); setPage(0); setSortBy(null); setSearch(""); }}
              className={`w-full text-left text-sm px-2 py-1.5 rounded flex justify-between items-center ${selected === t.name ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}
            >
              <span className="truncate">{t.name}</span>
              <span className={`text-xs ml-1 ${selected === t.name ? "text-primary-foreground/70" : "text-muted-foreground"}`}>{t.row_count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!selected ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Select a table from the sidebar to browse its contents.
          </div>
        ) : (
          <>
            {/* Toolbar */}
            <div className="flex items-center gap-3 mb-3 shrink-0">
              <h3 className="font-semibold text-lg">{selected}</h3>
              {tableData && <span className="text-sm text-muted-foreground">{tableData.total} rows</span>}
              <input
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(0); }}
                placeholder="Search..."
                className="border border-input rounded-md px-2 py-1 text-sm w-48 ml-auto"
              />
              <select value={pageSize} onChange={(e) => { setPageSize(+e.target.value); setPage(0); }} className="border border-input rounded-md px-3 py-1.5 text-sm bg-background">
                {[25, 50, 100].map((n) => <option key={n} value={n}>{n} rows</option>)}
              </select>
              <a href={`/api/db/tables/${selected}/export`} className="px-3 py-1 text-sm border rounded-md hover:bg-accent">
                Export CSV
              </a>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-auto border border-border rounded-md">
              {isLoading ? (
                <div className="p-8 text-center text-muted-foreground animate-pulse">Loading...</div>
              ) : tableData && tableData.rows.length > 0 ? (
                <table className="w-full text-sm">
                  <thead className="bg-muted sticky top-0">
                    <tr className="border-b">
                      {tableData.columns.map((col) => (
                        <th
                          key={col.name}
                          onClick={() => handleSort(col.name)}
                          className="text-left px-4 py-2.5 font-medium cursor-pointer hover:bg-accent select-none whitespace-nowrap"
                        >
                          {col.name}
                          {sortBy === col.name && <span className="ml-1 text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>}
                          <span className="block text-xs text-muted-foreground font-normal">{col.type}</span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.rows.map((row, i) => (
                      <tr key={i} className="border-b border-border hover:bg-accent/30">
                        {tableData.columns.map((col) => (
                          <td key={col.name} className="px-4 py-2.5 max-w-xs truncate" title={String(row[col.name] ?? "")}>
                            {formatCell(row[col.name])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-muted-foreground">No rows found.</div>
              )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-2 shrink-0 text-sm">
                <span className="text-muted-foreground">
                  Page {page + 1} of {totalPages}
                </span>
                <div className="flex gap-1">
                  <button onClick={() => setPage(0)} disabled={page === 0} className="px-2 py-1 border rounded disabled:opacity-30">First</button>
                  <button onClick={() => setPage(page - 1)} disabled={page === 0} className="px-2 py-1 border rounded disabled:opacity-30">Prev</button>
                  <button onClick={() => setPage(page + 1)} disabled={page >= totalPages - 1} className="px-2 py-1 border rounded disabled:opacity-30">Next</button>
                  <button onClick={() => setPage(totalPages - 1)} disabled={page >= totalPages - 1} className="px-2 py-1 border rounded disabled:opacity-30">Last</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return value.toLocaleString();
  const s = String(value);
  return s.length > 80 ? s.slice(0, 77) + "..." : s;
}
