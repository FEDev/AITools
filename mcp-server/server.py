"""
mcp-server/server.py — Model Context Protocol server exposing every tool in this repo.

For MCP-aware clients/agents (Claude Desktop, Claude Code, any MCP host). Uses the
official `mcp` Python SDK's FastMCP helper, which auto-generates the MCP tool schema
from each function's type hints + docstring.

Run (stdio transport, e.g. for Claude Desktop's mcp config):
    pip install -r requirements.txt
    python3 server.py

Run (HTTP/SSE transport, for remote / multi-client use):
    python3 server.py --http --port 8090
"""
import argparse
import os
import sys
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from ai_trader_tools import exchanges, mt_bridge, technical, sentiment, risk  # noqa: E402

mcp = FastMCP("ai-trader-tools")

# ---- market data / execution (crypto, via ccxt) ---------------------------------------
mcp.tool()(exchanges.get_ohlcv)
mcp.tool()(exchanges.get_ticker)
mcp.tool()(exchanges.get_order_book)
mcp.tool()(exchanges.get_balance)
mcp.tool()(exchanges.get_positions)
mcp.tool()(exchanges.place_order)
mcp.tool()(exchanges.cancel_order)

# ---- MT5 bridge (forex / XAUUSD) -------------------------------------------------------
mcp.tool()(mt_bridge.mt5_get_rates)
mcp.tool()(mt_bridge.mt5_place_order)
mcp.tool()(mt_bridge.mt5_get_positions)
mcp.tool()(mt_bridge.mt5_account_info)

# ---- technical analysis ----------------------------------------------------------------
mcp.tool()(technical.calc_rsi)
mcp.tool()(technical.calc_ema)
mcp.tool()(technical.calc_sma)
mcp.tool()(technical.calc_macd)
mcp.tool()(technical.calc_bollinger_bands)
mcp.tool()(technical.calc_atr)
mcp.tool()(technical.calc_adx)
mcp.tool()(technical.calc_stochastic)
mcp.tool()(technical.calc_ichimoku)

# ---- sentiment ---------------------------------------------------------------------------
mcp.tool()(sentiment.get_fear_greed_index)
mcp.tool()(sentiment.analyze_text_sentiment)
mcp.tool()(sentiment.fetch_news_headlines)

# ---- risk ----------------------------------------------------------------------------------
mcp.tool()(risk.calc_position_size)
mcp.tool()(risk.calc_risk_reward)
mcp.tool()(risk.calc_kelly_criterion)
mcp.tool()(risk.calc_max_drawdown)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Serve over HTTP/SSE instead of stdio")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()

    if args.http:
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
