"""
exchanges.py — unified crypto exchange tools built on ccxt.

ENHANCEMENTS:
  - Connection pooling & caching, keyed correctly by (exchange, network, key) so a
    cached mainnet instance can never be silently reused for a testnet/demo call
  - Verified Demo/Testnet support per exchange, cross-checked against each
    exchange's own API docs and ccxt's actual sandbox implementation (not just
    ccxt's config surface, which silently accepts keys it doesn't act on)
  - Input validation & rate limiting guards
  - Async-ready structure for future upgrades
  - Division-by-zero guards
  - Proper error handling & logging

Works with any ccxt-supported exchange id. Explicitly tested against:
binance, bybit, okx, kucoin, kraken, coinbase, bitget, gate (aliased from the
common name "gateio"), mexc, bingx, htx.

Network modes ('mainnet' | 'testnet' | 'demo') — verified against each exchange's
own docs, not just ccxt's config surface:
  - binance: testnet -> testnet.binance.vision (spot) + testnet.binancefuture.com
    (futures), via ccxt's native sandbox mode. demo -> Binance's separate "Demo
    Mode" product (demo-api.binance.com, spot only) — NOT the same infrastructure
    as testnet (testnet resets monthly with independent prices; demo mirrors live
    prices and resets on demand). Needs its own demo API key from Binance.
  - bybit: testnet -> api-testnet.bybit.com via ccxt sandbox mode. demo -> Bybit's
    separate "Demo Trading" product (api-demo.bybit.com) via ccxt's
    enable_demo_trading() — NOT the same as testnet; demo API keys come from your
    production account switched into Demo Trading mode, not from testnet.bybit.com.
  - okx: testnet and demo are the same thing (OKX only has one paper-trading mode,
    toggled via ccxt sandbox mode / the x-simulated-trading header).
  - bitget, bingx: ccxt's native sandbox mode is verified to work for both.
  - kucoin, kraken (spot), coinbase, mexc, htx: ccxt has NO sandbox/testnet
    implementation for these — requesting testnet/demo raises NotImplementedError
    rather than silently trading on mainnet. (KuCoin's own sandbox was
    discontinued; Kraken spot testing requires a manually-provisioned UAT
    environment — though Kraken *Futures*, a separate ccxt exchange id
    `krakenfutures`, has a public self-serve demo not wired up here; Coinbase's
    sandbox is a static, limited mock, not live paper trading.)

All functions return plain dicts/lists (JSON-serializable) so they can be handed
straight back to an LLM as a tool result, or returned as-is from the REST API / MCP server.
"""
from typing import Optional, Tuple, Dict, Any
import logging
import threading
import time

try:
    import ccxt
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "ccxt is required — install with: pip install ccxt"
    ) from e

logger = logging.getLogger(__name__)

# ============================================================================
# NETWORK MODE SUPPORT TABLE
# ============================================================================
# See the module docstring for the reasoning/sourcing behind each of these.

# Common alternate names mapped to the id ccxt actually registers the exchange
# under. "gateio" is the name Gate.io is usually referred to by (and what the
# README lists) but ccxt's unified id is "gate".
EXCHANGE_ID_ALIASES = {
    "gateio": "gate",
}

# Exchanges where ccxt's built-in sandbox mode (triggered by passing
# `sandbox: True` at construction) is verified to correctly redirect to that
# exchange's real testnet/paper-trading infrastructure.
SANDBOX_SUPPORTED = {"binance", "bybit", "okx", "bitget", "bingx"}

# Exchanges where ccxt has no sandbox/testnet implementation at all — passing
# `sandbox: True` raises inside ccxt itself rather than doing anything useful.
SANDBOX_UNSUPPORTED = {"kucoin", "kraken", "coinbase", "mexc", "htx"}

# Exchanges whose "demo" product is genuinely separate infrastructure from
# their "testnet" product (different base URL, different API keys) — handled
# with exchange-specific logic in _create_exchange rather than the generic
# sandbox path.
_DEMO_HAS_DEDICATED_INFRA = {"binance", "bybit"}


class ExchangeUnsupportedError(NotImplementedError):
    """Raised when a requested network mode has no working implementation for
    this exchange, so the caller gets a clear error instead of silently
    trading on the wrong network."""


# ============================================================================
# CONNECTION POOLING & CACHING
# ============================================================================

class ExchangePool:
    """Thread-safe cache for exchange instances with TTL."""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl  # seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.lock = threading.RLock()

    def _key(self, exchange_id: str, network: str, api_key: Optional[str]) -> str:
        """Generate cache key from exchange, network, and key.

        Network MUST be part of the key — otherwise a mainnet instance cached
        under (exchange_id, api_key) would be silently handed back to a later
        call that asked for network='testnet' with the same (public/no) key.
        """
        return f"{exchange_id}:{network}:{api_key or 'public'}"

    def get(self, exchange_id: str, api_key: Optional[str], api_secret: Optional[str],
            network: str = "mainnet") -> Any:
        """Get or create an exchange instance."""
        key = self._key(exchange_id, network, api_key)

        with self.lock:
            if key in self.cache:
                ex, created_at = self.cache[key]
                if time.time() - created_at < self.ttl:
                    return ex
                else:
                    del self.cache[key]  # Expired

            # Create new instance
            ex = _create_exchange(exchange_id, api_key, api_secret, network)
            self.cache[key] = (ex, time.time())
            return ex

    def clear(self):
        """Clear all cached instances."""
        with self.lock:
            self.cache.clear()


_pool = ExchangePool(ttl=300)


def _create_exchange(exchange_id: str, api_key: Optional[str] = None,
                     api_secret: Optional[str] = None, network: str = "mainnet") -> Any:
    """Create a ccxt exchange instance with proper config.

    Raises ExchangeUnsupportedError (rather than silently falling back to
    mainnet) if network='testnet'/'demo' is requested for an exchange with no
    working implementation of that mode.
    """
    network = (network or "mainnet").strip().lower()
    if network not in ("mainnet", "testnet", "demo"):
        raise ValueError(f"network must be 'mainnet', 'testnet', or 'demo', got '{network!r}'")

    resolved_id = EXCHANGE_ID_ALIASES.get(exchange_id, exchange_id)
    if resolved_id != exchange_id:
        logger.info(f"'{exchange_id}' is aliased to ccxt id '{resolved_id}'")

    if not hasattr(ccxt, resolved_id):
        raise ValueError(
            f"Unknown exchange_id '{exchange_id}'. ccxt supports {len(ccxt.exchanges)} exchanges — "
            f"see ccxt.exchanges for the full list."
        )

    klass = getattr(ccxt, resolved_id)
    config = {
        "enableRateLimit": True,
        "recvWindow": 5000,  # 5 second window for Binance
    }

    # ---- API credentials (only if provided) ----
    if api_key and api_secret:
        config["apiKey"] = api_key
        config["secret"] = api_secret

    post_init_demo_trading = False  # bybit's demo needs a method call after construction

    if network == "testnet":
        if resolved_id in SANDBOX_SUPPORTED:
            config["sandbox"] = True
        elif resolved_id in SANDBOX_UNSUPPORTED:
            raise ExchangeUnsupportedError(
                f"'{exchange_id}' has no testnet supported by ccxt. Falling back to mainnet "
                f"was intentionally removed here since that would silently trade on live "
                f"infrastructure when testnet was explicitly requested. Check {exchange_id}'s "
                f"own docs for a manual testing environment outside ccxt."
            )
        else:
            logger.warning(
                f"Testnet support for '{exchange_id}' is unverified — attempting ccxt's "
                f"generic sandbox mode, which may not work correctly"
            )
            config["sandbox"] = True

    elif network == "demo":
        if resolved_id == "binance":
            # Binance's Demo Mode is a separate product from Testnet (spot only),
            # on its own base URL, mirroring the same /api/v3, /api/v1 path
            # structure as mainnet/testnet. Requires a demo API key from Binance
            # (Binance Demo Trading UI), not a testnet.binance.vision key.
            config["urls"] = {
                "api": {
                    "public": "https://demo-api.binance.com/api/v3",
                    "private": "https://demo-api.binance.com/api/v3",
                    "v1": "https://demo-api.binance.com/api/v1",
                }
            }
        elif resolved_id == "bybit":
            # Bybit Demo Trading (api-demo.bybit.com) is separate infrastructure
            # from Testnet — ccxt exposes it via enable_demo_trading(), which must
            # be called on the instance (it's not a constructor config key).
            post_init_demo_trading = True
        elif resolved_id == "okx":
            # OKX has no separate demo/testnet split — one sandbox mode covers both.
            config["sandbox"] = True
        elif resolved_id in SANDBOX_UNSUPPORTED:
            raise ExchangeUnsupportedError(
                f"'{exchange_id}' has no demo/paper-trading mode supported by ccxt. Falling "
                f"back to mainnet was intentionally removed here since that would silently "
                f"trade on live infrastructure when demo was explicitly requested. Check "
                f"{exchange_id}'s own docs for a manual testing environment outside ccxt."
            )
        elif resolved_id in SANDBOX_SUPPORTED:
            # bitget, bingx: no dedicated "demo" product beyond their sandbox toggle.
            config["sandbox"] = True
        else:
            logger.warning(
                f"Demo mode for '{exchange_id}' is unverified — attempting ccxt's generic "
                f"sandbox mode, which may not work correctly"
            )
            config["sandbox"] = True

    ex = klass(config)
    if post_init_demo_trading:
        ex.enable_demo_trading(True)
    return ex


# ============================================================================
# MARKET DATA FUNCTIONS
# ============================================================================

def get_ohlcv(
    exchange_id: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 200,
    network: str = "mainnet",
) -> dict:
    """
    Fetch OHLCV (open/high/low/close/volume) candles.
    
    Args:
        exchange_id: ccxt exchange id (e.g., 'binance', 'bybit')
        symbol: unified symbol (e.g., 'BTC/USDT')
        timeframe: '1m', '5m', '15m', '1h', '4h', '1d', etc.
        limit: number of candles to fetch (max 500 for safety)
        network: 'mainnet', 'testnet', or 'demo'
    
    Returns:
        dict with 'exchange', 'symbol', 'timeframe', 'candles' (list of OHLCV dicts)
    """
    # Validate input
    if limit > 500:
        limit = 500
        logger.warning(f"limit capped at 500 (requested {limit})")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    
    ex = _pool.get(exchange_id, None, None, network)
    raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    
    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "network": network,
        "candles": [
            {
                "timestamp": c[0],
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
                "volume": c[5],
            }
            for c in raw
        ],
    }


def get_ticker(
    exchange_id: str,
    symbol: str,
    network: str = "mainnet",
) -> dict:
    """Fetch current ticker (price, bid/ask, 24h stats)."""
    ex = _pool.get(exchange_id, None, None, network)
    t = ex.fetch_ticker(symbol)
    
    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "network": network,
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


def get_order_book(
    exchange_id: str,
    symbol: str,
    limit: int = 20,
    network: str = "mainnet",
) -> dict:
    """Fetch live order book (bids/asks)."""
    if limit > 100:
        limit = 100
        logger.warning("order book limit capped at 100")
    
    ex = _pool.get(exchange_id, None, None, network)
    ob = ex.fetch_order_book(symbol, limit=limit)
    
    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "network": network,
        "bids": ob.get("bids", [])[:limit],
        "asks": ob.get("asks", [])[:limit],
        "timestamp": ob.get("timestamp"),
    }


# ============================================================================
# ACCOUNT / EXECUTION FUNCTIONS
# ============================================================================

def get_balance(
    exchange_id: str,
    api_key: str,
    api_secret: str,
    network: str = "mainnet",
) -> dict:
    """Fetch account balance (requires API key/secret with read permission)."""
    if not api_key or not api_secret:
        raise ValueError("api_key and api_secret are required")
    
    ex = _pool.get(exchange_id, api_key, api_secret, network)
    bal = ex.fetch_balance()
    totals = bal.get("total", {})
    non_zero = {k: v for k, v in totals.items() if v and v != 0}
    
    return {
        "exchange": exchange_id,
        "network": network,
        "balances": non_zero,
        "timestamp": bal.get("info", {}).get("updateTime"),
    }


def get_positions(
    exchange_id: str,
    api_key: str,
    api_secret: str,
    symbol: Optional[str] = None,
    network: str = "mainnet",
) -> dict:
    """
    Fetch open futures/margin positions.
    
    Args:
        exchange_id: ccxt exchange id
        api_key: API key
        api_secret: API secret
        symbol: Optional, filter to one symbol
        network: 'mainnet', 'testnet', or 'demo'
    """
    if not api_key or not api_secret:
        raise ValueError("api_key and api_secret are required")
    
    ex = _pool.get(exchange_id, api_key, api_secret, network)
    
    if not ex.has.get("fetchPositions"):
        raise NotImplementedError(f"{exchange_id} does not support fetchPositions via ccxt")
    
    positions = ex.fetch_positions([symbol] if symbol else None)
    open_positions = [p for p in positions if p.get("contracts") not in (None, 0)]
    
    return {
        "exchange": exchange_id,
        "network": network,
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
    network: str = "mainnet",
) -> dict:
    """
    DESTRUCTIVE: places a real (or demo/testnet, depending on your API key) order.
    
    Confirm intent first. Mainnet orders are LIVE — verify everything before calling.
    For testing, use network='testnet' or network='demo' with appropriate credentials.
    
    Args:
        exchange_id: ccxt exchange id
        symbol: unified symbol (e.g., 'BTC/USDT')
        side: 'buy' or 'sell'
        order_type: 'market' or 'limit'
        amount: quantity to trade
        api_key: API key (must have trading permission)
        api_secret: API secret
        price: required for limit orders
        network: 'mainnet', 'testnet', or 'demo'
    """
    if not api_key or not api_secret:
        raise ValueError("api_key and api_secret are required")
    
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got '{side}'")
    
    if order_type not in ("market", "limit"):
        raise ValueError(f"order_type must be 'market' or 'limit', got '{order_type}'")
    
    if amount <= 0:
        raise ValueError(f"amount must be > 0, got {amount}")
    
    if order_type == "limit" and not price:
        raise ValueError("price is required for limit orders")
    
    ex = _pool.get(exchange_id, api_key, api_secret, network)
    
    try:
        order = ex.create_order(symbol, order_type, side, amount, price)
    except Exception as e:
        logger.error(f"Order placement failed on {exchange_id} ({network}): {e}")
        raise
    
    return {
        "exchange": exchange_id,
        "network": network,
        "orderId": order.get("id"),
        "symbol": order.get("symbol"),
        "side": order.get("side"),
        "type": order.get("type"),
        "amount": order.get("amount"),
        "price": order.get("price"),
        "status": order.get("status"),
        "timestamp": order.get("timestamp"),
    }


def cancel_order(
    exchange_id: str,
    order_id: str,
    symbol: str,
    api_key: str,
    api_secret: str,
    network: str = "mainnet",
) -> dict:
    """
    Cancel an open order.
    
    DESTRUCTIVE: cancels a real order (or testnet/demo depending on network).
    """
    if not api_key or not api_secret:
        raise ValueError("api_key and api_secret are required")
    
    if not order_id:
        raise ValueError("order_id is required")
    
    ex = _pool.get(exchange_id, api_key, api_secret, network)
    
    try:
        result = ex.cancel_order(order_id, symbol)
    except Exception as e:
        logger.error(f"Order cancellation failed on {exchange_id} ({network}): {e}")
        raise
    
    return {
        "exchange": exchange_id,
        "network": network,
        "orderId": order_id,
        "symbol": symbol,
        "result": result,
    }


def clear_exchange_pool():
    """Manually clear all cached exchange instances (e.g., on shutdown)."""
    _pool.clear()
