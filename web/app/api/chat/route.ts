// Proxies the chat to the Python agent and streams the SSE response straight through.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const AGENT_URL = process.env.AGENT_URL ?? "http://localhost:8000";
const sseHeaders = { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" };

function sseError(message: string) {
  return new Response(`data: ${JSON.stringify({ type: "error", message })}\n\n`, { headers: sseHeaders });
}

export async function POST(req: Request) {
  try {
    const upstream = await fetch(`${AGENT_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: await req.text(),
      signal: req.signal,
      cache: "no-store",
    });
    if (!upstream.ok || !upstream.body) return sseError(`Agent returned HTTP ${upstream.status}.`);
    return new Response(upstream.body, { headers: sseHeaders });
  } catch {
    return sseError("Cannot reach the agent service. Start it with: uvicorn main:app --port 8000 (inside /agent).");
  }
}
