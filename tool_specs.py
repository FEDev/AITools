"""
tool_specs.py — SINGLE SOURCE OF TRUTH for every tool in this toolkit.

Every tool is declared ONCE here as a plain dict:
    {
        "name": "...",
        "description": "...",
        "parameters": { ...JSON Schema (object)... },
        "category": "...",
        "implementation": "python/ai_trader_tools/<module>.py::<function>"
    }

generate_manifests.py reads this list and emits:
    - openai_tools.json      (OpenAI Chat Completions / Responses API function-calling format)
    - anthropic_tools.json   (Anthropic Messages API tool-use format)
    - mcp_tools.json         (plain name/description/inputSchema, used by mcp-server/server.py)
    - llms.txt               (human + LLM readable catalog, markdown)

Add a new tool = add one dict here, then re-run generate_manifests.py.
Do NOT hand-edit the generated *.json / llms.txt files — edit this file instead.
"""

TOOLS = [
    # ---------------------------------------------------------------- MARKET DATA (crypto, via ccxt — 10+ exchanges) ----
    {
        "name": "get_ohlcv",
        "category": "market_data",
        "description": "Fetch OHLCV (open/high/low/close/volume) candles for a symbol on a crypto exchange. Works across Binance, Bybit, OKX, KuCoin, Kraken, Coinbase, Bitget, Gate.io, MEXC, BingX, HTX (Huobi) and any other ccxt-supported exchange.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string", "description": "ccxt exchange id, e.g. 'binance', 'bybit', 'okx', 'kraken'"},
                "symbol": {"type": "string", "description": "Unified symbol, e.g. 'BTC/USDT'"},
                "timeframe": {"type": "string", "description": "e.g. '1m','5m','15m','1h','4h','1d'", "default": "1h"},
                "limit": {"type": "integer", "description": "Number of candles to fetch", "default": 200},
            },
            "required": ["exchange_id", "symbol"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::get_ohlcv",
    },
    {
        "name": "get_ticker",
        "category": "market_data",
        "description": "Fetch the current ticker (last price, bid/ask, 24h stats) for a symbol on a crypto exchange.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string"},
                "symbol": {"type": "string"},
            },
            "required": ["exchange_id", "symbol"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::get_ticker",
    },
    {
        "name": "get_order_book",
        "category": "market_data",
        "description": "Fetch the live order book (bids/asks) for a symbol on a crypto exchange.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string"},
                "symbol": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["exchange_id", "symbol"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::get_order_book",
    },
    {
        "name": "get_balance",
        "category": "execution",
        "description": "Fetch account balance from a crypto exchange. Requires API key/secret with read permission.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string"},
                "api_key": {"type": "string"},
                "api_secret": {"type": "string"},
            },
            "required": ["exchange_id", "api_key", "api_secret"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::get_balance",
    },
    {
        "name": "get_positions",
        "category": "execution",
        "description": "Fetch open futures/margin positions from a crypto exchange.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string"},
                "api_key": {"type": "string"},
                "api_secret": {"type": "string"},
                "symbol": {"type": "string", "description": "Optional, filter to one symbol"},
            },
            "required": ["exchange_id", "api_key", "api_secret"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::get_positions",
    },
    {
        "name": "place_order",
        "category": "execution",
        "description": "Place a market or limit order on a crypto exchange. DESTRUCTIVE / trades real or demo funds — use with caution and confirm intent before calling.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string"},
                "symbol": {"type": "string"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "order_type": {"type": "string", "enum": ["market", "limit"]},
                "amount": {"type": "number"},
                "price": {"type": "number", "description": "Required for limit orders"},
                "api_key": {"type": "string"},
                "api_secret": {"type": "string"},
            },
            "required": ["exchange_id", "symbol", "side", "order_type", "amount", "api_key", "api_secret"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::place_order",
    },
    {
        "name": "cancel_order",
        "category": "execution",
        "description": "Cancel an open order on a crypto exchange by order id.",
        "parameters": {
            "type": "object",
            "properties": {
                "exchange_id": {"type": "string"},
                "order_id": {"type": "string"},
                "symbol": {"type": "string"},
                "api_key": {"type": "string"},
                "api_secret": {"type": "string"},
            },
            "required": ["exchange_id", "order_id", "symbol", "api_key", "api_secret"],
        },
        "implementation": "python/ai_trader_tools/exchanges.py::cancel_order",
    },
    # ---------------------------------------------------------------- MT4/MT5 BRIDGE (forex / XAUUSD) -------------------
    {
        "name": "mt5_get_rates",
        "category": "market_data_mt5",
        "description": "Fetch historical OHLC rates from a running MetaTrader 5 terminal (forex, XAUUSD, indices). Requires MT5 terminal installed and logged in on the host machine (Windows, or Wine).",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "e.g. 'XAUUSD', 'EURUSD'"},
                "timeframe": {"type": "string", "description": "e.g. 'M1','M5','M15','H1','H4','D1'", "default": "H1"},
                "count": {"type": "integer", "default": 200},
            },
            "required": ["symbol"],
        },
        "implementation": "python/ai_trader_tools/mt_bridge.py::mt5_get_rates",
    },
    {
        "name": "mt5_place_order",
        "category": "execution_mt5",
        "description": "Place a market order via a running MT5 terminal. DESTRUCTIVE — trades real or demo funds.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "order_type": {"type": "string", "enum": ["buy", "sell"]},
                "volume": {"type": "number", "description": "Lot size"},
                "sl": {"type": "number", "description": "Stop loss price, optional"},
                "tp": {"type": "number", "description": "Take profit price, optional"},
            },
            "required": ["symbol", "order_type", "volume"],
        },
        "implementation": "python/ai_trader_tools/mt_bridge.py::mt5_place_order",
    },
    {
        "name": "mt5_get_positions",
        "category": "execution_mt5",
        "description": "Fetch open positions from a running MT5 terminal.",
        "parameters": {"type": "object", "properties": {}},
        "implementation": "python/ai_trader_tools/mt_bridge.py::mt5_get_positions",
    },
    {
        "name": "mt5_account_info",
        "category": "execution_mt5",
        "description": "Fetch account balance/equity/margin info from a running MT5 terminal.",
        "parameters": {"type": "object", "properties": {}},
        "implementation": "python/ai_trader_tools/mt_bridge.py::mt5_account_info",
    },
    # ---------------------------------------------------------------- TECHNICAL ANALYSIS --------------------------------
    {
        "name": "calc_rsi",
        "category": "technical_analysis",
        "description": "Calculate Relative Strength Index (RSI) from a list of closing prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "closes": {"type": "array", "items": {"type": "number"}},
                "period": {"type": "integer", "default": 14},
            },
            "required": ["closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_rsi",
    },
    {
        "name": "calc_ema",
        "category": "technical_analysis",
        "description": "Calculate Exponential Moving Average (EMA) from a list of closing prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "closes": {"type": "array", "items": {"type": "number"}},
                "period": {"type": "integer", "default": 20},
            },
            "required": ["closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_ema",
    },
    {
        "name": "calc_sma",
        "category": "technical_analysis",
        "description": "Calculate Simple Moving Average (SMA) from a list of closing prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "closes": {"type": "array", "items": {"type": "number"}},
                "period": {"type": "integer", "default": 20},
            },
            "required": ["closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_sma",
    },
    {
        "name": "calc_macd",
        "category": "technical_analysis",
        "description": "Calculate MACD line, signal line and histogram from a list of closing prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "closes": {"type": "array", "items": {"type": "number"}},
                "fast_period": {"type": "integer", "default": 12},
                "slow_period": {"type": "integer", "default": 26},
                "signal_period": {"type": "integer", "default": 9},
            },
            "required": ["closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_macd",
    },
    {
        "name": "calc_bollinger_bands",
        "category": "technical_analysis",
        "description": "Calculate Bollinger Bands (upper/middle/lower) from a list of closing prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "closes": {"type": "array", "items": {"type": "number"}},
                "period": {"type": "integer", "default": 20},
                "std_dev": {"type": "number", "default": 2},
            },
            "required": ["closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_bollinger_bands",
    },
    {
        "name": "calc_atr",
        "category": "technical_analysis",
        "description": "Calculate Average True Range (ATR) from OHLC candles.",
        "parameters": {
            "type": "object",
            "properties": {
                "highs": {"type": "array", "items": {"type": "number"}},
                "lows": {"type": "array", "items": {"type": "number"}},
                "closes": {"type": "array", "items": {"type": "number"}},
                "period": {"type": "integer", "default": 14},
            },
            "required": ["highs", "lows", "closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_atr",
    },
    {
        "name": "calc_adx",
        "category": "technical_analysis",
        "description": "Calculate Average Directional Index (ADX) plus +DI/-DI from OHLC candles.",
        "parameters": {
            "type": "object",
            "properties": {
                "highs": {"type": "array", "items": {"type": "number"}},
                "lows": {"type": "array", "items": {"type": "number"}},
                "closes": {"type": "array", "items": {"type": "number"}},
                "period": {"type": "integer", "default": 14},
            },
            "required": ["highs", "lows", "closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_adx",
    },
    {
        "name": "calc_stochastic",
        "category": "technical_analysis",
        "description": "Calculate the Stochastic Oscillator (%K, %D) from OHLC candles.",
        "parameters": {
            "type": "object",
            "properties": {
                "highs": {"type": "array", "items": {"type": "number"}},
                "lows": {"type": "array", "items": {"type": "number"}},
                "closes": {"type": "array", "items": {"type": "number"}},
                "k_period": {"type": "integer", "default": 14},
                "d_period": {"type": "integer", "default": 3},
            },
            "required": ["highs", "lows", "closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_stochastic",
    },
    {
        "name": "calc_ichimoku",
        "category": "technical_analysis",
        "description": "Calculate Ichimoku Cloud components (tenkan, kijun, senkou A/B, chikou) from OHLC candles.",
        "parameters": {
            "type": "object",
            "properties": {
                "highs": {"type": "array", "items": {"type": "number"}},
                "lows": {"type": "array", "items": {"type": "number"}},
                "closes": {"type": "array", "items": {"type": "number"}},
            },
            "required": ["highs", "lows", "closes"],
        },
        "implementation": "python/ai_trader_tools/technical.py::calc_ichimoku",
    },
    # ---------------------------------------------------------------- SENTIMENT ------------------------------------------
    {
        "name": "get_fear_greed_index",
        "category": "sentiment",
        "description": "Fetch the crypto Fear & Greed Index (0=extreme fear, 100=extreme greed) from alternative.me. No API key required.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "How many past days to fetch", "default": 1}},
        },
        "implementation": "python/ai_trader_tools/sentiment.py::get_fear_greed_index",
    },
    {
        "name": "analyze_text_sentiment",
        "category": "sentiment",
        "description": "Run sentiment analysis (VADER, no API key needed) over a list of texts (headlines, tweets, posts) and return per-text and aggregate compound scores.",
        "parameters": {
            "type": "object",
            "properties": {
                "texts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["texts"],
        },
        "implementation": "python/ai_trader_tools/sentiment.py::analyze_text_sentiment",
    },
    {
        "name": "fetch_news_headlines",
        "category": "sentiment",
        "description": "Fetch recent news/crypto headlines for a query from a pluggable provider (NewsAPI, CryptoPanic, etc). Requires an API key for the chosen provider — bring your own key.",
        "parameters": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "enum": ["newsapi", "cryptopanic"], "default": "newsapi"},
                "query": {"type": "string"},
                "api_key": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["query", "api_key"],
        },
        "implementation": "python/ai_trader_tools/sentiment.py::fetch_news_headlines",
    },
    # ---------------------------------------------------------------- RISK -----------------------------------------------
    {
        "name": "calc_position_size",
        "category": "risk",
        "description": "Calculate position size given account balance, risk percentage per trade, entry price and stop-loss price.",
        "parameters": {
            "type": "object",
            "properties": {
                "account_balance": {"type": "number"},
                "risk_pct": {"type": "number", "description": "Risk per trade as percent, e.g. 1 for 1%"},
                "entry_price": {"type": "number"},
                "stop_loss_price": {"type": "number"},
            },
            "required": ["account_balance", "risk_pct", "entry_price", "stop_loss_price"],
        },
        "implementation": "python/ai_trader_tools/risk.py::calc_position_size",
    },
    {
        "name": "calc_risk_reward",
        "category": "risk",
        "description": "Calculate the risk/reward ratio for a trade given entry, stop-loss and take-profit prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_price": {"type": "number"},
                "stop_loss_price": {"type": "number"},
                "take_profit_price": {"type": "number"},
            },
            "required": ["entry_price", "stop_loss_price", "take_profit_price"],
        },
        "implementation": "python/ai_trader_tools/risk.py::calc_risk_reward",
    },
    {
        "name": "calc_kelly_criterion",
        "category": "risk",
        "description": "Calculate the Kelly Criterion optimal bet fraction given win rate and average win/loss size.",
        "parameters": {
            "type": "object",
            "properties": {
                "win_rate": {"type": "number", "description": "0-1"},
                "avg_win": {"type": "number"},
                "avg_loss": {"type": "number", "description": "Positive number"},
            },
            "required": ["win_rate", "avg_win", "avg_loss"],
        },
        "implementation": "python/ai_trader_tools/risk.py::calc_kelly_criterion",
    },
    {
        "name": "calc_max_drawdown",
        "category": "risk",
        "description": "Calculate maximum drawdown (and its percentage) from an equity curve.",
        "parameters": {
            "type": "object",
            "properties": {
                "equity_curve": {"type": "array", "items": {"type": "number"}},
            },
            "required": ["equity_curve"],
        },
        "implementation": "python/ai_trader_tools/risk.py::calc_max_drawdown",
    },
]

SUPPORTED_EXCHANGES = [
    "binance", "bybit", "okx", "kucoin", "kraken",
    "coinbase", "bitget", "gateio", "mexc", "bingx", "htx",
]
