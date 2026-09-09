"""
exchanges.py — unified crypto exchange tools built on ccxt.

Works with any ccxt-supported exchange id. Explicitly tested against:
binance, bybit, okx, kucoin, kraken, coinbase, bitget, gateio, mexc, bingx, htx.

All functions return plain dicts/lists (JSON-serializable) so they can be handed
straight back to an LLM as a tool result, or returned as-is from the REST API / MCP server.
"""
from typing import Optional

try:
    import ccxt
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "ccxt is required — install with: pip install ccxt"
    ) from e


def _get_exchange(exchange_id: str, api_key: Optional[str] = None, api_secret: Optional[str] = None):
    if not hasattr(ccxt, exchange_id):
        raise ValueError(
            f"Unknown exchange_id '{exchange_id}'. ccxt supports {len(ccxt.exchanges)} exchanges — "
            f"see ccxt.exchanges for the full list."
        )
    klass = getattr(ccxt, exchange_id)
    config = {"enableRateLimit": True}
    if api_key and api_secret:
        config["apiKey"] = api_key
        config["secret"] = api_secret
    return klass(config)


def get_ohlcv(exchange_id: str, symbol: str, timeframe: str = "1h", limit: int = 200) -> dict:
    ex = _get_exchange(exchange_id)
    raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": [
            {"timestamp": c[0], "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]}
            for c in raw
        ],
    }


def get_ticker(exchange_id: str, symbol: str) -> dict:
    ex = _get_exchange(exchange_id)
    t = ex.fetch_ticker(symbol)
    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "last": t.get("last"),
        "bid": t.get("bid"),
        "ask": t.get("ask"),
        "high": t.get("high"),
        "low": t.get("low"),
        "baseVolume": t.get("baseVolume"),
        "quoteVolume": t.get("quoteVolume"),
        "percentage": t.get("percentage"),
        "timestamp": t.get("timestamp"),
    }


def get_order_book(exchange_id: str, symbol: str, limit: int = 20) -> dict:
    ex = _get_exchange(exchange_id)
    ob = ex.fetch_order_book(symbol, limit=limit)
    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "bids": ob.get("bids", [])[:limit],
        "asks": ob.get("asks", [])[:limit],
        "timestamp": ob.get("timestamp"),
    }


def get_balance(exchange_id: str, api_key: str, api_secret: str) -> dict:
    ex = _get_exchange(exchange_id, api_key, api_secret)
    bal = ex.fetch_balance()
    totals = bal.get("total", {})
    non_zero = {k: v for k, v in totals.items() if v}
    return {"exchange": exchange_id, "balances": non_zero}


def get_positions(exchange_id: str, api_key: str, api_secret: str, symbol: Optional[str] = None) -> dict:
    ex = _get_exchange(exchange_id, api_key, api_secret)
    if not ex.has.get("fetchPositions"):
        raise NotImplementedError(f"{exchange_id} does not support fetchPositions via ccxt")
    positions = ex.fetch_positions([symbol] if symbol else None)
    open_positions = [p for p in positions if p.get("contracts") not in (None, 0)]
    return {
        "exchange": exchange_id,
        "positions": [
            {
                "symbol": p.get("symbol"),
                "side": p.get("side"),
                "contracts": p.get("contracts"),
                "entryPrice": p.get("entryPrice"),
                "markPrice": p.get("markPrice"),
                "unrealizedPnl": p.get("unrealizedPnl"),
                "leverage": p.get("leverage"),
            }
            for p in open_positions
        ],
    }


def place_order(
    exchange_id: str,
    symbol: str,
    side: str,
    order_type: str,
    amount: float,
    api_key: str,
    api_secret: str,
    price: Optional[float] = None,
) -> dict:
    """DESTRUCTIVE: places a real (or demo, depending on your API key) order. Confirm intent first."""
    ex = _get_exchange(exchange_id, api_key, api_secret)
    order = ex.create_order(symbol, order_type, side, amount, price)
    return {
        "exchange": exchange_id,
        "orderId": order.get("id"),
        "symbol": order.get("symbol"),
        "side": order.get("side"),
        "type": order.get("type"),
        "amount": order.get("amount"),
        "price": order.get("price"),
        "status": order.get("status"),
    }


def cancel_order(exchange_id: str, order_id: str, symbol: str, api_key: str, api_secret: str) -> dict:
    ex = _get_exchange(exchange_id, api_key, api_secret)
    result = ex.cancel_order(order_id, symbol)
    return {"exchange": exchange_id, "orderId": order_id, "symbol": symbol, "result": result}
