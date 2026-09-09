"""
Example: use ai_trader_tools directly in a Python app/agent, no server needed.

    pip install -r ../python/requirements.txt
    python3 python_direct_import.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from ai_trader_tools import exchanges, technical, sentiment, risk

if __name__ == "__main__":
    # 1. Pull recent candles from Binance (public endpoint, no API key needed for OHLCV)
    data = exchanges.get_ohlcv("binance", "BTC/USDT", timeframe="1h", limit=100)
    closes = [c["close"] for c in data["candles"]]

    # 2. Run technical analysis on it
    rsi = technical.calc_rsi(closes)
    macd = technical.calc_macd(closes)
    print("RSI(14):", rsi["latest"])
    print("MACD:", macd["latest"])

    # 3. Check market sentiment
    fng = sentiment.get_fear_greed_index()
    print("Fear & Greed:", fng["readings"][0])

    # 4. Size a hypothetical position
    sizing = risk.calc_position_size(account_balance=10_000, risk_pct=1, entry_price=closes[-1], stop_loss_price=closes[-1] * 0.98)
    print("Position size:", sizing)
