"""
technical.py — technical analysis indicators, pure pandas/numpy (no ta-lib compile step,
so it installs cleanly anywhere: pip install pandas numpy).

Every function takes plain lists (as an LLM tool call would supply) and returns plain
dicts/lists of floats — JSON-serializable, safe to hand straight back to an LLM.
"""
from typing import List

import numpy as np
import pandas as pd


def _clean(series: pd.Series) -> list:
    return [None if pd.isna(v) else round(float(v), 6) for v in series]


def calc_rsi(closes: List[float], period: int = 14) -> dict:
    s = pd.Series(closes, dtype=float)
    delta = s.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return {"period": period, "values": _clean(rsi), "latest": _clean(rsi)[-1] if len(rsi) else None}


def calc_ema(closes: List[float], period: int = 20) -> dict:
    s = pd.Series(closes, dtype=float)
    ema = s.ewm(span=period, adjust=False).mean()
    return {"period": period, "values": _clean(ema), "latest": _clean(ema)[-1] if len(ema) else None}


def calc_sma(closes: List[float], period: int = 20) -> dict:
    s = pd.Series(closes, dtype=float)
    sma = s.rolling(window=period).mean()
    return {"period": period, "values": _clean(sma), "latest": _clean(sma)[-1] if len(sma) else None}


def calc_macd(closes: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> dict:
    s = pd.Series(closes, dtype=float)
    ema_fast = s.ewm(span=fast_period, adjust=False).mean()
    ema_slow = s.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    hist = macd_line - signal_line
    return {
        "macd": _clean(macd_line),
        "signal": _clean(signal_line),
        "histogram": _clean(hist),
        "latest": {
            "macd": _clean(macd_line)[-1] if len(macd_line) else None,
            "signal": _clean(signal_line)[-1] if len(signal_line) else None,
            "histogram": _clean(hist)[-1] if len(hist) else None,
        },
    }


def calc_bollinger_bands(closes: List[float], period: int = 20, std_dev: float = 2) -> dict:
    s = pd.Series(closes, dtype=float)
    middle = s.rolling(window=period).mean()
    std = s.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return {
        "upper": _clean(upper), "middle": _clean(middle), "lower": _clean(lower),
        "latest": {
            "upper": _clean(upper)[-1] if len(upper) else None,
            "middle": _clean(middle)[-1] if len(middle) else None,
            "lower": _clean(lower)[-1] if len(lower) else None,
        },
    }


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def calc_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> dict:
    h, l, c = pd.Series(highs, dtype=float), pd.Series(lows, dtype=float), pd.Series(closes, dtype=float)
    tr = _true_range(h, l, c)
    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return {"period": period, "values": _clean(atr), "latest": _clean(atr)[-1] if len(atr) else None}


def calc_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> dict:
    h, l, c = pd.Series(highs, dtype=float), pd.Series(lows, dtype=float), pd.Series(closes, dtype=float)
    up_move = h.diff()
    down_move = -l.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = _true_range(h, l, c)
    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return {
        "period": period,
        "adx": _clean(adx), "plus_di": _clean(plus_di), "minus_di": _clean(minus_di),
        "latest": {
            "adx": _clean(adx)[-1] if len(adx) else None,
            "plus_di": _clean(plus_di)[-1] if len(plus_di) else None,
            "minus_di": _clean(minus_di)[-1] if len(minus_di) else None,
        },
    }


def calc_stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> dict:
    h, l, c = pd.Series(highs, dtype=float), pd.Series(lows, dtype=float), pd.Series(closes, dtype=float)
    lowest_low = l.rolling(window=k_period).min()
    highest_high = h.rolling(window=k_period).max()
    k = 100 * (c - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return {
        "k": _clean(k), "d": _clean(d),
        "latest": {"k": _clean(k)[-1] if len(k) else None, "d": _clean(d)[-1] if len(d) else None},
    }


def calc_ichimoku(highs: List[float], lows: List[float], closes: List[float]) -> dict:
    h, l, c = pd.Series(highs, dtype=float), pd.Series(lows, dtype=float), pd.Series(closes, dtype=float)
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    chikou = c.shift(-26)
    return {
        "tenkan_sen": _clean(tenkan), "kijun_sen": _clean(kijun),
        "senkou_span_a": _clean(senkou_a), "senkou_span_b": _clean(senkou_b),
        "chikou_span": _clean(chikou),
    }
