# ai-trader-tools

Open-source, MIT-licensed toolkit of **27 callable tools** for building AI/LLM-driven
trading agents — market data & execution across **11 crypto exchanges** (via ccxt) plus
an **MT5 bridge** for forex/XAUUSD, technical analysis, sentiment, and risk management.

Anyone can use it, fork it, or drop it into their own agent stack. No API keys are
bundled — bring your own exchange/broker/news credentials.

## Three ways to consume it (pick what fits your app)

| Method | Best for | Where |
|---|---|---|
| **Plain function-calling manifest** | Any standard LLM provider API (OpenAI, Anthropic, Azure OpenAI, Groq, etc) — not just agent frameworks | `tools-manifest/openai_tools.json`, `anthropic_tools.json` |
| **MCP server** | MCP-aware agents/hosts (Claude Desktop, Claude Code, etc) | `mcp-server/server.py` |
| **REST API** | Next.js, browser apps, curl, any HTTP-capable client/language | `rest-api/main.py` |
| **Direct import** | Python or Node apps that don't need a server | `python/ai_trader_tools`, `node/src` |

All four are generated from / dispatch to the **same 27 tools**, defined once in
`tools-manifest/tool_specs.py` so nothing drifts out of sync. See `llms.txt` at the repo
root for the full human+LLM-readable tool catalog — paste it straight into a system
prompt if you just want an LLM to "know" what's available.

## Quick start

### Option A — feed the manifest to a normal LLM API (no server)
```bash
pip install -r python/requirements.txt openai
export OPENAI_API_KEY=...
python3 examples/openai_function_calling.py
```
This is the "single file the AI can read" path: `tools-manifest/openai_tools.json` /
`anthropic_tools.json` is exactly the `tools=[...]` array these APIs expect. The model
picks a tool + arguments; you dispatch with `ai_trader_tools.registry.call_tool(name, **args)`.

### Option B — REST API (any language, e.g. Next.js)
```bash
cd rest-api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
# then: curl -X POST localhost:8080/tools/calc_rsi -d '{"closes":[...]}'
```
Or via Docker: `docker compose up rest-api`. See `examples/node_rest_client.js` and
`examples/nextjs-example/` for client code.

### Option C — MCP server (Claude Desktop / Claude Code / any MCP host)
```bash
cd mcp-server
pip install -r requirements.txt
python3 server.py                    # stdio transport
python3 server.py --http --port 8090 # HTTP/SSE transport, for remote use
```
Point your MCP client config at this command (stdio) or URL (HTTP).

### Option D — import directly
```python
# Python
from ai_trader_tools import exchanges, technical, sentiment, risk
data = exchanges.get_ohlcv("binance", "BTC/USDT", "1h", 200)
rsi = technical.calc_rsi([c["close"] for c in data["candles"]])
```
```ts
// Node / TypeScript
import { exchanges, technical } from "ai-trader-tools";
const data = await exchanges.getOhlcv("binance", "BTC/USDT", "1h", 200);
const rsi = technical.calcRsi(data.candles.map(c => c.close));
```

## What's included

- **Market data & execution (crypto)** — `get_ohlcv`, `get_ticker`, `get_order_book`,
  `get_balance`, `get_positions`, `place_order`, `cancel_order`. Built on
  [ccxt](https://github.com/ccxt/ccxt), unified across **binance, bybit, okx, kucoin,
  kraken, coinbase, bitget, gateio, mexc, bingx, htx** — swap `exchange_id` for any other
  ccxt-supported exchange (100+) with no code changes.
- **MT5 bridge (forex / XAUUSD / indices)** — `mt5_get_rates`, `mt5_place_order`,
  `mt5_get_positions`, `mt5_account_info`. Requires a running MetaTrader 5 terminal on
  the same machine (Windows or Wine) — see `python/ai_trader_tools/mt_bridge.py`.
- **Technical analysis** — RSI, EMA, SMA, MACD, Bollinger Bands, ATR, ADX, Stochastic,
  Ichimoku Cloud. Pure pandas/numpy in Python (no ta-lib compile step), the
  `technicalindicators` package in Node.
- **Sentiment** — `get_fear_greed_index` (real, free, no key), `analyze_text_sentiment`
  (VADER, real, no key), `fetch_news_headlines` (pluggable — NewsAPI / CryptoPanic, bring
  your own key, or add your own provider in `sentiment.py` / `sentiment.ts`).
- **Risk management** — `calc_position_size`, `calc_risk_reward`, `calc_kelly_criterion`,
  `calc_max_drawdown`.

## Repo layout

```
tools-manifest/     single source of truth (tool_specs.py) + generated manifests
python/              ai_trader_tools package — the reference implementation
node/                 TypeScript port (exchanges, technical, sentiment, risk)
rest-api/            FastAPI wrapper — POST /tools/{name}
mcp-server/          MCP server (stdio + HTTP/SSE)
examples/             direct-import, REST client, Next.js route, OpenAI function calling
llms.txt              full tool catalog, human + LLM readable
docker-compose.yml    run rest-api + mcp-server together
```

To add a new tool: add one entry to `tools-manifest/tool_specs.py`, implement it in
`python/ai_trader_tools/<module>.py` (and optionally `node/src/<module>.ts`), register it
in `python/ai_trader_tools/registry.py` and `mcp-server/server.py`, then run
`python3 tools-manifest/generate_manifests.py` to refresh the manifests.

## Extending exchange coverage

`exchange_id` is passed straight through to ccxt, so any of ccxt's 100+ supported
exchanges work immediately — the 11 listed above are just the ones called out
explicitly. Run `python3 -c "import ccxt; print(ccxt.exchanges)"` for the full list.

## Security notes

- No credentials are bundled or hard-coded anywhere. `api_key`/`api_secret`/`api_key`
  params are passed in by the caller per-call.
- `place_order`, `cancel_order`, and `mt5_place_order` are **destructive** — they submit
  real (or demo, depending on the keys you supply) orders. Gate these behind explicit
  confirmation in your agent loop.
- The REST API's CORS is wide open (`*`) by default for easy local development — restrict
  `allow_origins` in `rest-api/main.py` before exposing it publicly with live trading keys.

## Disclaimer

Educational, open-source infrastructure — not financial advice. Trading carries risk of
loss. You are responsible for how you use this code, including any live trading it executes.
