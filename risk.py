"""risk.py — position sizing and risk-management calculators. No external deps."""
from typing import List


def calc_position_size(account_balance: float, risk_pct: float, entry_price: float, stop_loss_price: float) -> dict:
    risk_amount = account_balance * (risk_pct / 100)
    price_risk_per_unit = abs(entry_price - stop_loss_price)
    if price_risk_per_unit == 0:
        raise ValueError("entry_price and stop_loss_price cannot be equal")
    position_size = risk_amount / price_risk_per_unit
    return {
        "risk_amount": round(risk_amount, 4),
        "price_risk_per_unit": round(price_risk_per_unit, 6),
        "position_size": round(position_size, 6),
        "notional_value": round(position_size * entry_price, 4),
    }


def calc_risk_reward(entry_price: float, stop_loss_price: float, take_profit_price: float) -> dict:
    risk = abs(entry_price - stop_loss_price)
    reward = abs(take_profit_price - entry_price)
    ratio = reward / risk if risk else None
    return {"risk": round(risk, 6), "reward": round(reward, 6), "risk_reward_ratio": round(ratio, 4) if ratio else None}


def calc_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> dict:
    if avg_loss <= 0:
        raise ValueError("avg_loss must be a positive number")
    b = avg_win / avg_loss
    kelly_fraction = win_rate - (1 - win_rate) / b
    return {
        "kelly_fraction": round(kelly_fraction, 4),
        "half_kelly_fraction": round(kelly_fraction / 2, 4),
        "note": "Most traders use half-Kelly or less to reduce variance/drawdown risk.",
    }


def calc_max_drawdown(equity_curve: List[float]) -> dict:
    if not equity_curve:
        raise ValueError("equity_curve must not be empty")
    peak = equity_curve[0]
    max_dd = 0.0
    max_dd_pct = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = peak - value
        dd_pct = (dd / peak) * 100 if peak else 0
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = dd_pct
    return {"max_drawdown": round(max_dd, 4), "max_drawdown_pct": round(max_dd_pct, 4)}
