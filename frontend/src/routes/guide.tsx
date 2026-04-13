import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import type { GuideSection } from "@/types";

export const Route = createFileRoute("/guide")({ component: Guide });

function Guide() {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(0);
  const { data: sections } = useQuery<GuideSection[]>({ queryKey: ["guide", "sections"], queryFn: () => api.get("/api/guide/sections") });
  const { data: results } = useQuery({ queryKey: ["guide", "search", search], queryFn: () => api.get<Array<{ title: string; snippet: string }>>(`/api/guide/search?q=${encodeURIComponent(search)}`), enabled: search.length >= 2 });

  if (!sections) return <div>Loading...</div>;

  return (
    <div className="flex gap-6">
      <aside className="w-56 space-y-1">
        <h2 className="font-bold text-lg mb-3">User Guide</h2>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search..." className="w-full border rounded px-2 py-1 text-sm mb-3" />
        {sections.map((s, i) => (
          <button key={i} onClick={() => { setSelected(i); setSearch(""); }} className={`block w-full text-left text-sm px-2 py-1 rounded ${selected === i && !search ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}>
            {s.title}
          </button>
        ))}
      </aside>

      <div className="flex-1 prose prose-sm max-w-none">
        {search && results ? (
          results.length > 0 ? results.map((r, i) => (
            <div key={i} className="mb-4 p-3 bg-card rounded-lg border border-border">
              <h3 className="font-semibold">{r.title}</h3>
              <p className="text-sm text-muted-foreground">{r.snippet}</p>
            </div>
          )) : <p className="text-muted-foreground">No results for "{search}"</p>
        ) : (
          <div dangerouslySetInnerHTML={{ __html: markdownToHtml(sections[selected]?.content || "") }} />
        )}
      </div>
    </div>
  );
}

function markdownToHtml(md: string): string {
  return md
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>")
    .replace(/\n\n/g, "<br/><br/>")
    .replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
}
