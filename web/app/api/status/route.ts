export const dynamic = "force-dynamic";

const AGENT_URL = process.env.AGENT_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const [health, metrics] = await Promise.all([
      fetch(`${AGENT_URL}/health`, { cache: "no-store" }).then((r) => r.json()),
      fetch(`${AGENT_URL}/metrics`, { cache: "no-store" }).then((r) => r.json()),
    ]);
    return Response.json({ online: true, ...health, metrics });
  } catch {
    return Response.json({ online: false, metrics: [] });
  }
}
