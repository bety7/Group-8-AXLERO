import type { Status } from "@/lib/types";

export default function Sidebar({ status }: { status: Status | null }) {
  const measures = status?.metrics.filter((m) => m.kind === "measure") ?? [];
  const dims = status?.metrics.filter((m) => m.kind === "dimension" && m.type !== "time" && m.name !== "orders.order_id") ?? [];
  const ok = status?.online && status.semantic_layer === "ok";

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-r border-line bg-card md:flex">
      <div className="px-5 pb-4 pt-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight">MetricMind</h1>
        <p className="mt-1 text-sm text-mute">Answers come from governed metric definitions, never from raw tables.</p>
      </div>

      <div className="flex items-center gap-2 border-y border-line px-5 py-2.5 text-sm">
        <span className={`h-2 w-2 rounded-full ${ok ? "bg-[#168a73]" : "bg-flag"}`} aria-hidden />
        <span>{status === null ? "Checking services..." : ok ? `Semantic layer online (${status.llm_provider})` : status.online ? "Semantic layer is down" : "Agent offline"}</span>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 text-sm">
        <h2 className="mb-2 font-medium">Metrics you can ask about</h2>
        <ul className="space-y-2">
          {measures.map((m) => (
            <li key={m.name} title={m.description}>
              <p className="font-medium">{m.title}</p>
              <p className="text-xs leading-snug text-mute">{m.description}</p>
            </li>
          ))}
        </ul>
        <h2 className="mb-2 mt-6 font-medium">Break down by</h2>
        <p className="leading-relaxed text-mute">{dims.map((d) => d.title).join(", ") || "-"}, and time</p>
      </div>
    </aside>
  );
}
