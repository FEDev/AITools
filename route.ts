/**
 * Example Next.js (App Router) API route: app/api/trader-tools/route.ts
 *
 * Proxies tool calls from your frontend to the ai-trader-tools REST API, so your
 * exchange API keys never reach the browser. Set AI_TRADER_TOOLS_URL in .env.local.
 *
 * Usage from the client:
 *   fetch('/api/trader-tools', {
 *     method: 'POST',
 *     body: JSON.stringify({ tool: 'calc_rsi', params: { closes: [...] } })
 *   })
 */
import { NextRequest, NextResponse } from "next/server";

const TOOLS_API_URL = process.env.AI_TRADER_TOOLS_URL || "http://localhost:8080";

export async function POST(req: NextRequest) {
  const { tool, params } = await req.json();
  if (!tool) {
    return NextResponse.json({ error: "Missing 'tool' in request body" }, { status: 400 });
  }
  const resp = await fetch(`${TOOLS_API_URL}/tools/${tool}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params || {}),
  });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}

// Alternative: import the Node package directly instead of proxying to the REST API —
//   import { technical } from "ai-trader-tools";
//   const rsi = technical.calcRsi(closes);
// Use the REST proxy above when you want one shared backend for Python + Node + browser
// clients; import the package directly when this Next.js app IS the only consumer.
