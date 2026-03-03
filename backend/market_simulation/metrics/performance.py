"""Performance metric utilities for backtests."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import List, Sequence, Tuple


@dataclass
class PerformanceSeries:
    strategy: str
    equity_curve: List[Tuple[date, float]]  # ordered by date
    initial_nav: float


@dataclass
class PerformanceMetrics:
    cumulative_return: float
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    recovery_time_days: int


def _daily_returns(equity_curve: Sequence[Tuple[date, float]]) -> List[float]:
    rets: List[float] = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1][1]
        curr = equity_curve[i][1]
        if prev == 0:
            continue
        rets.append((curr / prev) - 1.0)
    return rets


def compute_metrics(series: PerformanceSeries, risk_free: float = 0.0) -> PerformanceMetrics:
    if not series.equity_curve:
        return PerformanceMetrics(0, 0, 0, 0, 0)

    equity = series.equity_curve
    initial = equity[0][1]
    final = equity[-1][1]
    cumulative_return = (final / initial) - 1.0 if initial != 0 else 0.0

    # Max drawdown and recovery time
    peak = equity[0][1]
    max_dd = 0.0
    recovery_time = 0
    temp_recovery = 0
    in_drawdown = False
    for _, nav in equity[1:]:
        if nav > peak:
            peak = nav
            in_drawdown = False
            temp_recovery = 0
        else:
            drawdown = (peak - nav) / peak if peak != 0 else 0
            if drawdown > 0:
                in_drawdown = True
                temp_recovery += 1
            if drawdown > max_dd:
                max_dd = drawdown
        if not in_drawdown:
            recovery_time = max(recovery_time, temp_recovery)
            temp_recovery = 0

    # Volatility and Sharpe (daily, annualized by sqrt(252))
    rets = _daily_returns(equity)
    if rets:
        mean_ret = sum(rets) / len(rets)
        var = sum((r - mean_ret) ** 2 for r in rets) / len(rets)
        vol = math.sqrt(var) * math.sqrt(252)
        sharpe = ((mean_ret - risk_free / 252) / (math.sqrt(var) if var > 0 else 1)) * math.sqrt(252) if var > 0 else 0.0
    else:
        vol = 0.0
        sharpe = 0.0

    return PerformanceMetrics(
        cumulative_return=cumulative_return,
        max_drawdown=max_dd,
        volatility=vol,
        sharpe_ratio=sharpe,
        recovery_time_days=recovery_time,
    )
