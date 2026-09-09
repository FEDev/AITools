"""
mt_bridge.py — bridge to a running MetaTrader 5 terminal, for forex / XAUUSD / indices.

REQUIRES:
  - MetaTrader 5 terminal installed and logged into a broker account (demo or live)
    on the SAME machine this code runs on (Windows natively, or Windows-under-Wine on
    Linux/Mac — the MetaTrader5 python package talks to the terminal over local IPC,
    it cannot connect to a remote terminal).
  - pip install MetaTrader5

If the terminal isn't available (e.g. running this on a Linux server with no MT5
installed), every function here raises a clear RuntimeError rather than failing silently.
For a headless/server setup, run this module on a Windows VM/VPS next to the terminal
and expose it over the REST API or MCP server included in this repo.
"""
from typing import Optional

try:
    import MetaTrader5 as mt5
    _MT5_AVAILABLE = True
except ImportError:
    _MT5_AVAILABLE = False

_TIMEFRAME_MAP = {
    "M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15", "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1", "H4": "TIMEFRAME_H4", "D1": "TIMEFRAME_D1", "W1": "TIMEFRAME_W1", "MN1": "TIMEFRAME_MN1",
}


def _require_mt5():
    if not _MT5_AVAILABLE:
        raise RuntimeError(
            "MetaTrader5 package not installed or not usable on this OS. "
            "Install with 'pip install MetaTrader5' on a Windows machine (or Wine) "
            "that has the MT5 terminal running and logged in."
        )
    if not mt5.initialize():
        raise RuntimeError(f"mt5.initialize() failed: {mt5.last_error()}. Is the MT5 terminal running and logged in?")


def mt5_get_rates(symbol: str, timeframe: str = "H1", count: int = 200) -> dict:
    _require_mt5()
    tf_const = getattr(mt5, _TIMEFRAME_MAP.get(timeframe, "TIMEFRAME_H1"))
    rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, count)
    if rates is None:
        raise RuntimeError(f"copy_rates_from_pos returned None: {mt5.last_error()}")
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": [
            {
                "time": int(r["time"]), "open": float(r["open"]), "high": float(r["high"]),
                "low": float(r["low"]), "close": float(r["close"]), "volume": int(r["tick_volume"]),
            }
            for r in rates
        ],
    }


def mt5_place_order(symbol: str, order_type: str, volume: float, sl: Optional[float] = None, tp: Optional[float] = None) -> dict:
    """DESTRUCTIVE: places a real (or demo) market order via the connected MT5 terminal."""
    _require_mt5()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"No tick data for symbol '{symbol}' — check it's in Market Watch.")
    price = tick.ask if order_type == "buy" else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": 20,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "type_time": mt5.ORDER_TIME_GTC,
    }
    if sl:
        request["sl"] = sl
    if tp:
        request["tp"] = tp
    result = mt5.order_send(request)
    return {
        "retcode": result.retcode,
        "order": result.order,
        "symbol": symbol,
        "type": order_type,
        "volume": volume,
        "price": price,
        "comment": result.comment,
    }


def mt5_get_positions() -> dict:
    _require_mt5()
    positions = mt5.positions_get()
    return {
        "positions": [
            {
                "ticket": p.ticket, "symbol": p.symbol,
                "type": "buy" if p.type == 0 else "sell",
                "volume": p.volume, "price_open": p.price_open,
                "price_current": p.price_current, "profit": p.profit,
                "sl": p.sl, "tp": p.tp,
            }
            for p in (positions or [])
        ]
    }


def mt5_account_info() -> dict:
    _require_mt5()
    info = mt5.account_info()
    if info is None:
        raise RuntimeError(f"account_info() returned None: {mt5.last_error()}")
    return {
        "login": info.login, "balance": info.balance, "equity": info.equity,
        "margin": info.margin, "margin_free": info.margin_free,
        "currency": info.currency, "leverage": info.leverage,
    }
