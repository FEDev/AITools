"""
registry.py — maps every tool name (as declared in tools-manifest/tool_specs.py) to its
actual Python callable. This is what rest-api/main.py and mcp-server/server.py both import
so a tool call coming from an LLM (by name + kwargs) can be dispatched generically.
"""
from . import exchanges, mt_bridge, technical, sentiment, risk

TOOL_REGISTRY = {
    # market data / execution (crypto)
    "get_ohlcv": exchanges.get_ohlcv,
    "get_ticker": exchanges.get_ticker,
    "get_order_book": exchanges.get_order_book,
    "get_balance": exchanges.get_balance,
    "get_positions": exchanges.get_positions,
    "place_order": exchanges.place_order,
    "cancel_order": exchanges.cancel_order,
    # mt5 bridge (forex / XAUUSD)
    "mt5_get_rates": mt_bridge.mt5_get_rates,
    "mt5_place_order": mt_bridge.mt5_place_order,
    "mt5_get_positions": mt_bridge.mt5_get_positions,
    "mt5_account_info": mt_bridge.mt5_account_info,
    # technical analysis
    "calc_rsi": technical.calc_rsi,
    "calc_ema": technical.calc_ema,
    "calc_sma": technical.calc_sma,
    "calc_macd": technical.calc_macd,
    "calc_bollinger_bands": technical.calc_bollinger_bands,
    "calc_atr": technical.calc_atr,
    "calc_adx": technical.calc_adx,
    "calc_stochastic": technical.calc_stochastic,
    "calc_ichimoku": technical.calc_ichimoku,
    # sentiment
    "get_fear_greed_index": sentiment.get_fear_greed_index,
    "analyze_text_sentiment": sentiment.analyze_text_sentiment,
    "fetch_news_headlines": sentiment.fetch_news_headlines,
    # risk
    "calc_position_size": risk.calc_position_size,
    "calc_risk_reward": risk.calc_risk_reward,
    "calc_kelly_criterion": risk.calc_kelly_criterion,
    "calc_max_drawdown": risk.calc_max_drawdown,
}


def call_tool(name: str, **kwargs):
    """Dispatch a tool call by name. Raises KeyError if the tool doesn't exist."""
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Unknown tool '{name}'. Available: {sorted(TOOL_REGISTRY)}")
    return TOOL_REGISTRY[name](**kwargs)
