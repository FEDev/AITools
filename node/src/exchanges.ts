/**
 * exchanges.ts — unified crypto exchange tools built on ccxt (JS). Mirrors
 * ../../python/ai_trader_tools/exchanges.py 1:1 so behaviour matches across languages.
 */
import ccxt, { Exchange } from "ccxt";

function getExchange(exchangeId: string, apiKey?: string, apiSecret?: string): Exchange {
  const klass = (ccxt as any)[exchangeId];
  if (!klass) {
    throw new Error(`Unknown exchange_id '${exchangeId}'. See ccxt.exchanges for the full list.`);
  }
  const config: Record<string, any> = { enableRateLimit: true };
  if (apiKey && apiSecret) {
    config.apiKey = apiKey;
    config.secret = apiSecret;
  }
  return new klass(config);
}

export async function getOhlcv(exchangeId: string, symbol: string, timeframe = "1h", limit = 200) {
  const ex = getExchange(exchangeId);
  const raw = await ex.fetchOHLCV(symbol, timeframe, undefined, limit);
  return {
    exchange: exchangeId,
    symbol,
    timeframe,
    candles: raw.map((c) => ({ timestamp: c[0], open: c[1], high: c[2], low: c[3], close: c[4], volume: c[5] })),
  };
}

export async function getTicker(exchangeId: string, symbol: string) {
  const ex = getExchange(exchangeId);
  const t = await ex.fetchTicker(symbol);
  return {
    exchange: exchangeId,
    symbol,
    last: t.last,
    bid: t.bid,
    ask: t.ask,
    high: t.high,
    low: t.low,
    baseVolume: t.baseVolume,
    quoteVolume: t.quoteVolume,
    percentage: t.percentage,
    timestamp: t.timestamp,
  };
}

export async function getOrderBook(exchangeId: string, symbol: string, limit = 20) {
  const ex = getExchange(exchangeId);
  const ob = await ex.fetchOrderBook(symbol, limit);
  return { exchange: exchangeId, symbol, bids: ob.bids.slice(0, limit), asks: ob.asks.slice(0, limit), timestamp: ob.timestamp };
}

export async function getBalance(exchangeId: string, apiKey: string, apiSecret: string) {
  const ex = getExchange(exchangeId, apiKey, apiSecret);
  const bal = await ex.fetchBalance();
  const totals = (bal as any).total || {};
  const nonZero = Object.fromEntries(Object.entries(totals).filter(([, v]) => v));
  return { exchange: exchangeId, balances: nonZero };
}

export async function getPositions(exchangeId: string, apiKey: string, apiSecret: string, symbol?: string) {
  const ex = getExchange(exchangeId, apiKey, apiSecret);
  if (!ex.has["fetchPositions"]) {
    throw new Error(`${exchangeId} does not support fetchPositions via ccxt`);
  }
  const positions = await ex.fetchPositions(symbol ? [symbol] : undefined);
  const open = positions.filter((p: any) => p.contracts);
  return {
    exchange: exchangeId,
    positions: open.map((p: any) => ({
      symbol: p.symbol,
      side: p.side,
      contracts: p.contracts,
      entryPrice: p.entryPrice,
      markPrice: p.markPrice,
      unrealizedPnl: p.unrealizedPnl,
      leverage: p.leverage,
    })),
  };
}

/** DESTRUCTIVE: places a real (or demo) order. Confirm intent before calling. */
export async function placeOrder(
  exchangeId: string,
  symbol: string,
  side: "buy" | "sell",
  orderType: "market" | "limit",
  amount: number,
  apiKey: string,
  apiSecret: string,
  price?: number
) {
  const ex = getExchange(exchangeId, apiKey, apiSecret);
  const order = await ex.createOrder(symbol, orderType, side, amount, price);
  return {
    exchange: exchangeId,
    orderId: order.id,
    symbol: order.symbol,
    side: order.side,
    type: order.type,
    amount: order.amount,
    price: order.price,
    status: order.status,
  };
}

export async function cancelOrder(exchangeId: string, orderId: string, symbol: string, apiKey: string, apiSecret: string) {
  const ex = getExchange(exchangeId, apiKey, apiSecret);
  const result = await ex.cancelOrder(orderId, symbol);
  return { exchange: exchangeId, orderId, symbol, result };
}

export const SUPPORTED_EXCHANGES = ["binance", "bybit", "okx", "kucoin", "kraken", "coinbase", "bitget", "gateio", "mexc", "bingx", "htx"];
