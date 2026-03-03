"""Strategy comparison runner for deterministic backtesting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List

from market_simulation.events.bus import EventBus
from market_simulation.metrics.performance import PerformanceMetrics, PerformanceSeries, compute_metrics
from market_simulation.portfolio.store import Portfolio
from market_simulation.replay.engine import ReplayConfig, ReplayEngine
from market_simulation.replay.price_store import PriceStore
from market_simulation.replay.trade_queue import TradeQueue
from market_simulation.strategy.base import Strategy


@dataclass
class StrategyResult:
    name: str
    equity_curve: List[tuple[date, float]]
    metrics: PerformanceMetrics


class StrategyComparisonRunner:
    def __init__(
        self,
        price_store: PriceStore,
        start_date: date,
        end_date: date,
        universe: Iterable[str],
        initial_cash: float = 100000.0,
    ) -> None:
        self.price_store = price_store
        self.start_date = start_date
        self.end_date = end_date
        self.universe = list(universe)
        self.initial_cash = initial_cash

    def run(self, strategies: List[Strategy]) -> Dict[str, StrategyResult]:
        results: Dict[str, StrategyResult] = {}
        for strat in strategies:
            bus = EventBus()
            equity: List[tuple[date, float]] = []
            bus.subscribe("snapshot", lambda ev, eq=equity: eq.append((ev.date, ev.nav)))

            portfolio = Portfolio(cash=self.initial_cash)
            trade_queue = TradeQueue()

            # Wrap strategy to inject orders pre-close each day using on_day hook
            class StrategyAwareReplayEngine(ReplayEngine):
                def _execute_day(self_inner, trade_date: date) -> None:
                    prices = self_inner.price_store.get_ohlc(trade_date, symbols=self_inner.config.universe)
                    # Strategy decides on orders for this day
                    strat.on_day(trade_date, prices, self_inner.portfolio, self_inner.trade_queue)
                    super()._execute_day(trade_date)

            cfg = ReplayConfig(
                sim_id=f"sim-{strat.name}",
                start_date=self.start_date,
                end_date=self.end_date,
                universe=self.universe,
            )
            engine = StrategyAwareReplayEngine(
                config=cfg,
                price_store=self.price_store,
                portfolio=portfolio,
                trade_queue=trade_queue,
                event_bus=bus,
            )
            engine.run_until_end()

            series = PerformanceSeries(strategy=strat.name, equity_curve=equity, initial_nav=self.initial_cash)
            metrics = compute_metrics(series)
            results[strat.name] = StrategyResult(name=strat.name, equity_curve=equity, metrics=metrics)
        return results

    @staticmethod
    def dashboard_payload(results: Dict[str, StrategyResult]) -> Dict[str, dict]:
        """Format results for dashboards: time series and summary metrics."""
        payload: Dict[str, dict] = {}
        for name, res in results.items():
            payload[name] = {
                "equity_curve": [{"date": d.isoformat(), "nav": nav} for d, nav in res.equity_curve],
                "metrics": {
                    "cumulative_return": res.metrics.cumulative_return,
                    "max_drawdown": res.metrics.max_drawdown,
                    "volatility": res.metrics.volatility,
                    "sharpe_ratio": res.metrics.sharpe_ratio,
                    "recovery_time_days": res.metrics.recovery_time_days,
                },
            }
        return payload

    @staticmethod
    def optimization_tips() -> List[str]:
        return [
            "Batch price lookups across strategies to reuse caches.",
            "Run strategies in parallel processes sharing a read-only price store.",
            "Snapshot after major intervals to resume without full replay.",
            "Reuse computed daily returns to avoid recomputing metrics per strategy.",
        ]
