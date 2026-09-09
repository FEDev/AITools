# ai-trader-tools

Open-source, MIT-licensed **backend tool library for AI/LLM-driven trading agents**.
It is not a trading bot or a strategy by itself — it's the set of callable functions
(market data, order execution, technical indicators, sentiment, risk sizing) that an
LLM-based agent, a custom bot, or your own backend calls to actually *do* things: pull
candles, check a Fear & Greed reading, size a position, or place/cancel an order.

Use it to:
- Give an LLM agent (OpenAI, Anthropic, or any function-calling API) real trading tools
  it can call by name, instead of writing exchange integration code yourself.
- Power a custom trading bot's data/execution layer without hand-rolling ccxt/MT5
  plumbing for every exchange.
- Back a Next.js, Node, or Python app that needs live crypto/forex data or order
  execution behind a simple REST/MCP interface.
- Prototype and paper-test strategy logic against real exchange testnet/demo
  environments before risking live capital (see **Network Modes** below — this is the
  part that needs the most care, since it's what stands between "testing" and "live").

**27 tools** across market data & execution on **11 named crypto exchanges** (via
[ccxt](https://github.com/ccxt/ccxt); any of ccxt's 100+ exchanges work by id), an
**MT5 bridge** for forex/XAUUSD/indices, technical analysis, sentiment, and risk
management. Anyone can use it, fork it, or drop it into their own agent stack. No API
keys are bundled — bring your own exchange/broker/news credentials.

See `CHANGELOG.md` for the repo's history, including a from-the-ground-up
restructuring and a set of correctness fixes to network-mode handling (mainnet vs.
testnet vs. demo) that are worth reading before you trade real funds against this.

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
  kraken, coinbase, bitget, gateio (aliased to ccxt's `gate`), mexc, bingx, htx** — swap
  `exchange_id` for any other ccxt-supported exchange (100+) with no code changes. Every
  function also takes a `network` param (`mainnet`/`testnet`/`demo`) — see **Network
  modes** below before running this against anything other than mainnet.
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

## Network modes: mainnet / testnet / demo

Every crypto exchange function (`get_ohlcv`, `get_ticker`, `get_order_book`,
`get_balance`, `get_positions`, `place_order`, `cancel_order`) takes a `network`
parameter: `"mainnet"` (default, live), `"testnet"`, or `"demo"`.

**Support is verified per-exchange against each exchange's own docs and ccxt's actual
implementation — not assumed.** "Testnet" and "demo" are genuinely different products
on some exchanges (different base URL, different API keys) and the same thing on
others; using the wrong one, or an exchange that doesn't support either, can silently
route calls to live infrastructure if not handled carefully. This table is current as
of the last fix to `exchanges.py`:

| Exchange | Testnet | Demo | Notes |
|---|---|---|---|
| `binance` | ✅ | ✅ | Testnet = `testnet.binance.vision` (spot) + `testnet.binancefuture.com` (futures), independent prices, resets monthly. Demo = separate "Demo Mode" product (`demo-api.binance.com`, spot only), mirrors live prices, resets on demand. **These require different API keys from each other and from mainnet** — get testnet keys from testnet.binance.vision, demo keys from Binance's Demo Trading UI. |
| `bybit` | ✅ | ✅ | Testnet (`api-testnet.bybit.com`) and Demo Trading (`api-demo.bybit.com`) are separate infrastructure with separate API keys — demo keys come from your production account switched into Demo Trading mode, not from testnet.bybit.com. Do not mix the two up. |
| `okx` | ✅ | ✅ | One paper-trading mode covers both — `network="testnet"` and `network="demo"` behave identically on OKX. |
| `bitget` | ✅ | ✅ | Native ccxt sandbox support. |
| `bingx` | ✅ | ✅ | Native ccxt sandbox support. |
| `kucoin` | ❌ | ❌ | ccxt has no sandbox implementation for KuCoin, and KuCoin's own public sandbox has been discontinued. Requesting testnet/demo raises `ExchangeUnsupportedError`. |
| `kraken` | ❌ | ❌ | ccxt has no sandbox implementation for Kraken spot. Kraken's spot UAT environment is manual/by-request via your account manager, not self-service. (Kraken *Futures* — a separate ccxt id, `krakenfutures` — has a public self-serve demo at `demo-futures.kraken.com`, not wired up in this repo.) Requesting testnet/demo raises `ExchangeUnsupportedError`. |
| `coinbase` | ❌ | ❌ | Coinbase's sandbox (`api-sandbox.coinbase.com`) is a static mock with pre-defined responses for Accounts/Orders only — not a live paper-trading environment — and ccxt doesn't wire it up. Requesting testnet/demo raises `ExchangeUnsupportedError`. |
| `mexc` | ❌ | ❌ | No ccxt sandbox implementation. Requesting testnet/demo raises `ExchangeUnsupportedError`. |
| `htx` | ❌ | ❌ | No ccxt sandbox implementation. Requesting testnet/demo raises `ExchangeUnsupportedError`. |
| `gateio` | — | — | Not a valid ccxt id — automatically aliased to ccxt's real id, `gate`. Use either name; `gateio` is kept for convenience since it's the name most people search for. |

For the 5 exchanges with no working testnet/demo, this toolkit deliberately raises an
error instead of silently falling back to mainnet — if you request `network="testnet"`
on one of them, you'll get a clear `ExchangeUnsupportedError`, not a live order.

The `ExchangePool` connection cache keys instances by `(exchange, network, api_key)`,
so a cached mainnet connection can never be silently reused for a testnet/demo call
(or vice versa).

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
