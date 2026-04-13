import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useRef, useEffect } from "react";
import { api } from "@/api/client";
import type { ChatSession, ChatMessage } from "@/types";
import { Trash2 } from "lucide-react";

export const Route = createFileRoute("/advisor")({ component: Advisor });

const ADVISORS = [
  { key: "boglehead", label: "Boglehead" },
  { key: "tax", label: "Tax" },
  { key: "muni", label: "Muni Bonds" },
] as const;

function Advisor() {
  const qc = useQueryClient();
  const [advisor, setAdvisor] = useState<string>("boglehead");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);

  const { data: sessions } = useQuery<ChatSession[]>({ queryKey: ["chat", "sessions", advisor], queryFn: () => api.get(`/api/chat/sessions?advisor_type=${advisor}`) });
  const { data: messages } = useQuery<ChatMessage[]>({ queryKey: ["chat", "messages", sessionId], queryFn: () => api.get(`/api/chat/sessions/${sessionId}/messages`), enabled: !!sessionId });

  const send = useMutation({
    mutationFn: (msg: string) => api.post<{ session_id: number; response: string }>("/api/chat/message", { message: msg, advisor_type: advisor, session_id: sessionId }),
    onSuccess: (data) => {
      setSessionId(data.session_id);
      qc.invalidateQueries({ queryKey: ["chat"] });
    },
  });

  const deleteSession = useMutation({
    mutationFn: (id: number) => api.delete(`/api/chat/sessions/${id}`),
    onSuccess: (_data, id) => {
      if (sessionId === id) setSessionId(null);
      qc.invalidateQueries({ queryKey: ["chat"] });
    },
  });

  useEffect(() => { messagesEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, send.data]);

  const handleSend = () => {
    if (!input.trim()) return;
    send.mutate(input);
    setInput("");
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">AI Advisor</h1>

      <div className="flex border-b border-border">
        {ADVISORS.map((a) => (
          <button key={a.key} onClick={() => { setAdvisor(a.key); setSessionId(null); }} className={`px-4 py-2 text-sm -mb-px border-b-2 transition-colors ${advisor === a.key ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"}`}>
            {a.label}
          </button>
        ))}
      </div>

      <div className="flex gap-4 h-[60vh]">
        <div className="w-48 border-r border-border pr-4 overflow-y-auto space-y-1">
          <button onClick={() => setSessionId(null)} className="text-sm text-primary font-medium w-full text-left py-1">+ New Chat</button>
          {sessions?.map((s) => (
            <div key={s.id} className={`group flex items-center rounded ${sessionId === s.id ? "bg-accent" : "hover:bg-accent/50"}`}>
              <button onClick={() => setSessionId(s.id)} className="flex-1 text-xs text-left py-1.5 px-2 truncate">
                {s.title || `Chat #${s.id}`}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); if (confirm("Delete this chat?")) deleteSession.mutate(s.id); }}
                className="md:opacity-0 md:group-hover:opacity-100 p-1 mr-1 text-muted-foreground hover:text-destructive active:text-destructive transition-opacity"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>

        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto space-y-3 mb-4">
            {messages?.map((m) => (
              <div key={m.id} className={`p-3 rounded-lg max-w-[80%] ${m.role === "user" ? "bg-primary text-primary-foreground ml-auto" : "bg-secondary"}`}>
                <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              </div>
            ))}
            {send.isPending && <div className="bg-secondary p-3 rounded-lg text-sm animate-pulse">Thinking...</div>}
            {send.data && !send.isPending && (
              <div className="bg-secondary p-3 rounded-lg max-w-[80%]"><p className="text-sm whitespace-pre-wrap">{send.data.response}</p></div>
            )}
            <div ref={messagesEnd} />
          </div>

          <div className="flex gap-2">
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} placeholder="Ask the advisor..." className="flex-1 border border-input rounded-md px-3 py-2" disabled={send.isPending} />
            <button onClick={handleSend} disabled={send.isPending} className="bg-primary text-primary-foreground px-4 py-2 rounded-md disabled:opacity-50">Send</button>
          </div>
        </div>
      </div>
    </div>
  );
}
