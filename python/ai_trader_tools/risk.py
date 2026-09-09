"""
risk.py — position sizing and risk-management calculators.

ENHANCEMENTS:
  - Input validation (bounds checking, type checking)
  - Guards against division by zero and edge cases
  - Better error messages for debugging
  - Detailed return values with metadata

No external deps beyond stdlib.
"""
from typing import List
import logging

logger = logging.getLogger(__name__)


def calc_position_size(
    account_balance: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
) -> dict:
    """
    Calculate position size given account balance and risk parameters.
    
    Args:
        account_balance: total account balance
        risk_pct: risk per trade as percentage (e.g., 1.0 for 1%)
        entry_price: entry price
        stop_loss_price: stop loss price
    
    Returns:
        dict with 'risk_amount', 'price_risk_per_unit', 'position_size', 'notional_value'
    """
    if account_balance <= 0:
        raise ValueError(f"account_balance must be > 0, got {account_balance}")
    if risk_pct <= 0 or risk_pct > 100:
        raise ValueError(f"risk_pct must be between 0 and 100, got {risk_pct}")
    if entry_price <= 0:
        raise ValueError(f"entry_price must be > 0, got {entry_price}")
    if stop_loss_price <= 0:
        raise ValueError(f"stop_loss_price must be > 0, got {stop_loss_price}")
    
    price_risk_per_unit = abs(entry_price - stop_loss_price)
    
    if price_risk_per_unit == 0:
        raise ValueError(
            f"entry_price ({entry_price}) and stop_loss_price ({stop_loss_price}) "
            "cannot be equal — no risk defined"
        )
    
    risk_amount = account_balance * (risk_pct / 100)
    position_size = risk_amount / price_risk_per_unit
    notional_value = position_size * entry_price
    
    return {
        "account_balance": round(account_balance, 4),
        "risk_pct": round(risk_pct, 4),
        "risk_amount": round(risk_amount, 4),
        "price_risk_per_unit": round(price_risk_per_unit, 8),
        "position_size": round(position_size, 8),
        "notional_value": round(notional_value, 4),
    }


def calc_risk_reward(
    entry_price: float,
    stop_loss_price: float,
    take_profit_price: float,
) -> dict:
    """
    Calculate risk/reward ratio for a trade.
    
    Args:
        entry_price: entry price
        stop_loss_price: stop loss price
        take_profit_price: take profit price
    
    Returns:
        dict with 'risk', 'reward', 'risk_reward_ratio'
    """
    if entry_price <= 0:
        raise ValueError(f"entry_price must be > 0, got {entry_price}")
    if stop_loss_price <= 0:
        raise ValueError(f"stop_loss_price must be > 0, got {stop_loss_price}")
    if take_profit_price <= 0:
        raise ValueError(f"take_profit_price must be > 0, got {take_profit_price}")
    
    risk = abs(entry_price - stop_loss_price)
    reward = abs(take_profit_price - entry_price)
    
    if risk == 0:
        logger.warning("Risk is 0 (entry == stop_loss); ratio will be None")
        ratio = None
    else:
        ratio = reward / risk
    
    return {
        "entry_price": round(entry_price, 8),
        "stop_loss_price": round(stop_loss_price, 8),
        "take_profit_price": round(take_profit_price, 8),
        "risk": round(risk, 8),
        "reward": round(reward, 8),
        "risk_reward_ratio": round(ratio, 4) if ratio else None,
    }


def calc_kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
) -> dict:
    """
    Calculate Kelly Criterion optimal fraction.
    
    Formula: f* = (b*p - q) / b
    where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
    
    Args:
        win_rate: fraction of winning trades (0-1)
        avg_win: average size of winning trade
        avg_loss: average size of losing trade (positive number)
    
    Returns:
        dict with 'kelly_fraction', 'half_kelly_fraction', and notes
    """
    if not (0 <= win_rate <= 1):
        raise ValueError(f"win_rate must be between 0 and 1, got {win_rate}")
    if avg_win <= 0:
        raise ValueError(f"avg_win must be > 0, got {avg_win}")
    if avg_loss <= 0:
        raise ValueError(f"avg_loss must be > 0, got {avg_loss}")
    
    b = avg_win / avg_loss
    kelly_fraction = win_rate - (1 - win_rate) / b
    
    # Kelly fraction can be negative (system has negative expectancy)
    # or > 1 (very aggressive). Clamp for practical use.
    half_kelly = kelly_fraction / 2
    
    interpretation = "invalid"
    if kelly_fraction < 0:
        interpretation = "negative expectancy (system loses money)"
    elif kelly_fraction == 0:
        interpretation = "break-even"
    elif 0 < kelly_fraction < 0.25:
        interpretation = "conservative"
    elif 0.25 <= kelly_fraction < 0.5:
        interpretation = "moderate"
    else:
        interpretation = "aggressive"
    
    return {
        "win_rate": round(win_rate, 4),
        "avg_win": round(avg_win, 8),
        "avg_loss": round(avg_loss, 8),
        "kelly_fraction": round(kelly_fraction, 4),
        "half_kelly_fraction": round(half_kelly, 4),
        "interpretation": interpretation,
        "note": "Most traders use half-Kelly or less to reduce variance/drawdown risk.",
    }


def calc_max_drawdown(equity_curve: List[float]) -> dict:
    """
    Calculate maximum drawdown (absolute and percentage) from an equity curve.
    
    Args:
        equity_curve: list of equity values over time
    
    Returns:
        dict with 'max_drawdown', 'max_drawdown_pct', 'start_value', 'end_value'
    """
    if not equity_curve:
        raise ValueError("equity_curve must not be empty")
    if len(equity_curve) < 2:
        raise ValueError("equity_curve must have at least 2 values")
    
    # Validate all values are numbers
    try:
        equity_curve = [float(v) for v in equity_curve]
    except (ValueError, TypeError) as e:
        raise ValueError(f"All equity_curve values must be numeric: {e}")
    
    peak = equity_curve[0]
    max_dd = 0.0
    max_dd_pct = 0.0
    peak_idx = 0
    trough_idx = 0
    
    for idx, value in enumerate(equity_curve):
        if value > peak:
            peak = value
            peak_idx = idx
        
        dd = peak - value
        dd_pct = (dd / peak) * 100 if peak > 0 else 0
        
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = dd_pct
            trough_idx = idx
    
    return {
        "start_value": round(equity_curve[0], 8),
        "end_value": round(equity_curve[-1], 8),
        "peak_value": round(peak, 8),
        "peak_index": peak_idx,
        "trough_index": trough_idx,
        "max_drawdown": round(max_dd, 8),
        "max_drawdown_pct": round(max_dd_pct, 4),
        "recovery_needed_pct": round((max_dd / peak) * 100 if peak > 0 else 0, 4),
    }
