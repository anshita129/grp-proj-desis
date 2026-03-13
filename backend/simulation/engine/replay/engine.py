"""Replay engine for time-travel simulation.

Executes trades at historical close prices, advances time deterministically,
recalculates portfolio, and emits valuation snapshots per step.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

from simulation.engine.events.bus import AuditEvent, EventBus, ValuationSnapshotEvent
from simulation.engine.portfolio.store import Portfolio
from simulation.engine.replay.price_store import OHLC, PriceStore
from simulation.engine.replay.time_state import TimeState
from simulation.engine.replay.trade_queue import ScheduledOrder, TradeQueue


@dataclass
class ReplayConfig:
    sim_id: str
    start_date: date
    end_date: date
    universe: Iterable[str]
    strict_missing_prices: bool = False
    scenario_id: str | None = None


class ReplayEngine:
    def __init__(
        self,
        config: ReplayConfig,
        price_store: PriceStore,
        portfolio: Portfolio,
        trade_queue: TradeQueue,
        event_bus: EventBus,
        time_state: TimeState | None = None,
    ) -> None:
        self.config = config
        self.price_store = price_store
        self.portfolio = portfolio
        self.trade_queue = trade_queue
        self.event_bus = event_bus
        self.time_state = time_state or TimeState(current_date=config.start_date, end_date=config.end_date)
        self.finished = False

    def _resolve_trade_date(self, target: date) -> Optional[date]:
        trade_date = self.price_store.next_trading_day_on_or_after(target)
        if trade_date is None:
            return None
        if trade_date > self.config.end_date:
            return None
        return trade_date

    def _execute_day(self, trade_date: date) -> None:
        prices = self.price_store.get_ohlc(trade_date, symbols=self.config.universe)
        # Execute queued trades up to trade_date at the close price
        for order in self.trade_queue.pop_until(trade_date):
            px = prices.get(order.symbol)
            if px is None:
                if self.config.strict_missing_prices:
                    raise ValueError(f"Missing price for {order.symbol} on {trade_date}")
                self.event_bus.publish(
                    "audit",
                    AuditEvent(
                        sim_id=self.config.sim_id,
                        date=trade_date,
                        message="missing_price",
                        payload={"symbol": order.symbol},
                    ),
                )
                continue
            self.portfolio.apply_fill(order, px.close, trade_date)

        # Re-mark to market (uses latest prices)
        self.portfolio.mark_to_market(prices, trade_date)

        snap = self.portfolio.snapshot(prices)
        self.event_bus.publish(
            "snapshot",
            ValuationSnapshotEvent(
                sim_id=self.config.sim_id,
                date=trade_date,
                nav=snap["nav"],
                cash=snap["cash"],
                positions=snap["positions"],
            ),
        )
        self.event_bus.publish(
            "audit",
            AuditEvent(
                sim_id=self.config.sim_id,
                date=trade_date,
                message="step_complete",
                payload={"nav": snap["nav"], "cash": snap["cash"]},
            ),
        )

    def step(self) -> Optional[date]:
        if self.finished or self.time_state.finished:
            return None
        target = self.time_state.now()
        trade_date = self._resolve_trade_date(target)
        if trade_date is None:
            self.finished = True
            self.time_state.mark_finished()
            return None
        self._execute_day(trade_date)
        # Advance calendar day (not trading day) to preserve determinism over weekends/holidays
        self.time_state.advance_calendar_day()
        return trade_date

    def jump_to(self, target_date: date) -> Optional[date]:
        """Advance sequentially until reaching target_date (inclusive)."""
        last_processed: Optional[date] = None
        while not self.finished and not self.time_state.finished:
            if self.time_state.now() > target_date:
                break
            processed = self.step()
            if processed is None:
                break
            last_processed = processed
        return last_processed

    def run_until_end(self) -> Optional[date]:
        last: Optional[date] = None
        while not self.finished and not self.time_state.finished:
            processed = self.step()
            if processed is None:
                break
            last = processed
        return last
