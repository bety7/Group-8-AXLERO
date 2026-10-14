"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { readEvents } from "@/lib/stream";
import type { Message, Status, StreamEvent } from "@/lib/types";
import ResultCard from "./ResultCard";
import Sidebar from "./Sidebar";

const SUGGESTIONS = [
  "Why did our European margins drop last quarter?",
  "Show me European sales by quarter",
  "Compare gross margin % across regions last quarter",
  "Which product categories drive the most revenue?",
];

function apply(msg: Message, ev: StreamEvent): Message {
  switch (ev.type) {
    case "token": {
      const last = msg.parts[msg.parts.length - 1];
      if (last?.type === "text") return { ...msg, parts: [...msg.parts.slice(0, -1), { type: "text", text: last.text + ev.text }] };
      return { ...msg, parts: [...msg.parts, { type: "text", text: ev.text }] };
    }
    case "tool_start":
      return { ...msg, parts: [...msg.parts, { type: "tool", id: ev.id, status: "running", args: ev.args }] };
    case "tool_result": {
      const { type: _t, id, ...result } = ev;
      return { ...msg, parts: msg.parts.map((p) => (p.type === "tool" && p.id === id ? { ...p, status: result.ok ? "done" : "error", result } : p)) };
    }
    case "error":
      return { ...msg, error: ev.message };
    default:
      return msg;
  }
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/status").then((r) => r.json()).then(setStatus).catch(() => setStatus({ online: false, metrics: [] }));
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    const user: Message = { id: crypto.randomUUID(), role: "user", parts: [{ type: "text", text: question }] };
    const assistant: Message = { id: crypto.randomUUID(), role: "assistant", parts: [] };
    const history = [...messages, user].map((m) => ({
      role: m.role,
      content: m.parts.filter((p) => p.type === "text").map((p) => (p as { text: string }).text).join("\n"),
    })).filter((m) => m.content);

    setMessages((prev) => [...prev, user, assistant]);
    setInput("");
    setBusy(true);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ messages: history }), signal: controller.signal });
      for await (const ev of readEvents(res)) {
        setMessages((prev) => prev.map((m) => (m.id === assistant.id ? apply(m, ev) : m)));
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setMessages((prev) => prev.map((m) => (m.id === assistant.id ? { ...m, error: "Connection lost. Check that the agent is running." } : m)));
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar status={status} />

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-3xl px-5 py-8">
            {messages.length === 0 ? (
              <div className="pt-[10vh]">
                <h2 className="font-display text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
                  Ask about the business. The numbers will match finance.
                </h2>
                <p className="mt-4 max-w-xl text-mute">
                  Every figure is computed from the shared metric definitions, so Finance and Sales see the same answer. Open &quot;View SQL&quot; on any result to check how it was calculated.
                </p>
                <div className="mt-8 flex flex-col items-start gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} onClick={() => send(s)} className="rounded-md border border-line bg-card px-4 py-2.5 text-left text-[15px] hover:border-accent">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="mb-6 flex justify-end">
                    <p className="max-w-[85%] rounded-lg bg-ink px-4 py-2.5 text-[15.5px] text-paper">{(m.parts[0] as { text: string }).text}</p>
                  </div>
                ) : (
                  <div key={m.id} className="mb-8">
                    {m.parts.map((p, i) =>
                      p.type === "text" ? (
                        <div key={i} className="md"><ReactMarkdown>{p.text}</ReactMarkdown></div>
                      ) : (
                        <ResultCard key={p.id} part={p} />
                      ),
                    )}
                    {busy && m === messages[messages.length - 1] && !m.parts.length && !m.error && (
                      <div className="thinking py-2" aria-label="Thinking"><span /><span /><span /></div>
                    )}
                    {m.error && <p role="alert" className="mt-2 rounded border border-flag/40 bg-flag/5 px-3 py-2 text-sm text-flag">{m.error}</p>}
                  </div>
                ),
              )
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="border-t border-line bg-paper px-5 py-4">
          <div className="mx-auto flex max-w-3xl gap-2">
            <input
              value={input} onChange={(e) => setInput(e.target.value)} disabled={busy}
              placeholder="Ask a question, e.g. Why did our European margins drop last quarter?"
              aria-label="Your question"
              className="min-w-0 flex-1 rounded-md border border-line bg-card px-4 py-2.5 text-[15.5px] placeholder:text-mute disabled:opacity-60"
            />
            {busy ? (
              <button type="button" onClick={() => abortRef.current?.abort()} className="rounded-md border border-ink px-4 py-2.5 text-sm font-medium">Stop</button>
            ) : (
              <button type="submit" disabled={!input.trim()} className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-white disabled:opacity-40">Ask</button>
            )}
          </div>
        </form>
      </main>
    </div>
  );
}
