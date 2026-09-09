/** risk.ts — position sizing and risk-management calculators. No external deps. Mirrors risk.py. */

export function calcPositionSize(accountBalance: number, riskPct: number, entryPrice: number, stopLossPrice: number) {
  const riskAmount = accountBalance * (riskPct / 100);
  const priceRiskPerUnit = Math.abs(entryPrice - stopLossPrice);
  if (priceRiskPerUnit === 0) throw new Error("entryPrice and stopLossPrice cannot be equal");
  const positionSize = riskAmount / priceRiskPerUnit;
  return {
    risk_amount: round(riskAmount, 4),
    price_risk_per_unit: round(priceRiskPerUnit, 6),
    position_size: round(positionSize, 6),
    notional_value: round(positionSize * entryPrice, 4),
  };
}

export function calcRiskReward(entryPrice: number, stopLossPrice: number, takeProfitPrice: number) {
  const risk = Math.abs(entryPrice - stopLossPrice);
  const reward = Math.abs(takeProfitPrice - entryPrice);
  const ratio = risk ? reward / risk : null;
  return { risk: round(risk, 6), reward: round(reward, 6), risk_reward_ratio: ratio !== null ? round(ratio, 4) : null };
}

export function calcKellyCriterion(winRate: number, avgWin: number, avgLoss: number) {
  if (avgLoss <= 0) throw new Error("avgLoss must be a positive number");
  const b = avgWin / avgLoss;
  const kellyFraction = winRate - (1 - winRate) / b;
  return {
    kelly_fraction: round(kellyFraction, 4),
    half_kelly_fraction: round(kellyFraction / 2, 4),
    note: "Most traders use half-Kelly or less to reduce variance/drawdown risk.",
  };
}

export function calcMaxDrawdown(equityCurve: number[]) {
  if (!equityCurve.length) throw new Error("equityCurve must not be empty");
  let peak = equityCurve[0];
  let maxDd = 0;
  let maxDdPct = 0;
  for (const value of equityCurve) {
    if (value > peak) peak = value;
    const dd = peak - value;
    const ddPct = peak ? (dd / peak) * 100 : 0;
    if (dd > maxDd) {
      maxDd = dd;
      maxDdPct = ddPct;
    }
  }
  return { max_drawdown: round(maxDd, 4), max_drawdown_pct: round(maxDdPct, 4) };
}

function round(v: number, digits: number) {
  const f = Math.pow(10, digits);
  return Math.round(v * f) / f;
}
