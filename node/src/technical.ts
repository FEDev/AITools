/**
 * technical.ts — technical analysis indicators, using the `technicalindicators` npm package.
 * Mirrors ../../python/ai_trader_tools/technical.py's function names/shapes.
 */
import {
  RSI, EMA, SMA, MACD, BollingerBands, ATR, ADX, Stochastic, IchimokuCloud,
} from "technicalindicators";

export function calcRsi(closes: number[], period = 14) {
  const values = RSI.calculate({ period, values: closes });
  return { period, values, latest: values.length ? values[values.length - 1] : null };
}

export function calcEma(closes: number[], period = 20) {
  const values = EMA.calculate({ period, values: closes });
  return { period, values, latest: values.length ? values[values.length - 1] : null };
}

export function calcSma(closes: number[], period = 20) {
  const values = SMA.calculate({ period, values: closes });
  return { period, values, latest: values.length ? values[values.length - 1] : null };
}

export function calcMacd(closes: number[], fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
  const out = MACD.calculate({
    values: closes, fastPeriod, slowPeriod, signalPeriod,
    SimpleMAOscillator: false, SimpleMASignal: false,
  });
  const macd = out.map((o) => o.MACD ?? null);
  const signal = out.map((o) => o.signal ?? null);
  const histogram = out.map((o) => o.histogram ?? null);
  const last = out[out.length - 1] || {};
  return { macd, signal, histogram, latest: { macd: last.MACD ?? null, signal: last.signal ?? null, histogram: last.histogram ?? null } };
}

export function calcBollingerBands(closes: number[], period = 20, stdDev = 2) {
  const out = BollingerBands.calculate({ period, values: closes, stdDev });
  const upper = out.map((o) => o.upper);
  const middle = out.map((o) => o.middle);
  const lower = out.map((o) => o.lower);
  const last = out[out.length - 1];
  return { upper, middle, lower, latest: last ? { upper: last.upper, middle: last.middle, lower: last.lower } : null };
}

export function calcAtr(highs: number[], lows: number[], closes: number[], period = 14) {
  const values = ATR.calculate({ period, high: highs, low: lows, close: closes });
  return { period, values, latest: values.length ? values[values.length - 1] : null };
}

export function calcAdx(highs: number[], lows: number[], closes: number[], period = 14) {
  const out = ADX.calculate({ period, high: highs, low: lows, close: closes });
  const adx = out.map((o) => o.adx);
  const plusDi = out.map((o) => o.pdi);
  const minusDi = out.map((o) => o.mdi);
  const last = out[out.length - 1];
  return { period, adx, plus_di: plusDi, minus_di: minusDi, latest: last ? { adx: last.adx, plus_di: last.pdi, minus_di: last.mdi } : null };
}

export function calcStochastic(highs: number[], lows: number[], closes: number[], kPeriod = 14, dPeriod = 3) {
  const out = Stochastic.calculate({ high: highs, low: lows, close: closes, period: kPeriod, signalPeriod: dPeriod });
  const k = out.map((o) => o.k);
  const d = out.map((o) => o.d);
  const last = out[out.length - 1];
  return { k, d, latest: last ? { k: last.k, d: last.d } : null };
}

export function calcIchimoku(highs: number[], lows: number[], closes: number[]) {
  const out = IchimokuCloud.calculate({ high: highs, low: lows, conversionPeriod: 9, basePeriod: 26, spanPeriod: 52, displacement: 26 });
  return {
    tenkan_sen: out.map((o) => o.conversion),
    kijun_sen: out.map((o) => o.base),
    senkou_span_a: out.map((o) => o.spanA),
    senkou_span_b: out.map((o) => o.spanB),
    note: "chikou_span omitted — technicalindicators' IchimokuCloud doesn't emit it; derive as closes shifted -26 if needed.",
  };
}
