/**
 * Example: any plain Node script (or Express/Fastify backend) calling the REST API.
 * Works identically from Next.js API routes, Deno, Bun, etc — it's just HTTP.
 *
 * Run the REST API first:
 *   cd ../rest-api && pip install -r requirements.txt && uvicorn main:app --port 8080
 * Then:
 *   node node_rest_client.js
 */
const BASE_URL = process.env.AI_TRADER_TOOLS_URL || "http://localhost:8080";

async function callTool(name, params) {
  const resp = await fetch(`${BASE_URL}/tools/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!resp.ok) throw new Error(`${name} failed: ${resp.status} ${await resp.text()}`);
  return (await resp.json()).result;
}

async function main() {
  const ohlcv = await callTool("get_ohlcv", { exchange_id: "binance", symbol: "BTC/USDT", timeframe: "1h", limit: 100 });
  const closes = ohlcv.candles.map((c) => c.close);

  const rsi = await callTool("calc_rsi", { closes });
  console.log("RSI(14):", rsi.latest);

  const fng = await callTool("get_fear_greed_index", { limit: 1 });
  console.log("Fear & Greed:", fng.readings[0]);

  const sizing = await callTool("calc_position_size", {
    account_balance: 10000, risk_pct: 1, entry_price: closes.at(-1), stop_loss_price: closes.at(-1) * 0.98,
  });
  console.log("Position size:", sizing);
}

main().catch(console.error);
