"""Strategy abstraction for deterministic backtesting."""
from __future__ import annotations

from datetime import date
from typing import Protocol

from market_simulation.replay.price_store import OHLC
from market_simulation.replay.trade_queue import TradeQueue
from market_simulation.portfolio.store import Portfolio


class Strategy(Protocol):
    name: str

    def on_day(self, day: date, prices: dict[str, OHLC], portfolio: Portfolio, trade_queue: TradeQueue) -> None:
        """Hook invoked once per trading day before close-execution.

        A strategy may enqueue orders for execution on `day` by adding to `trade_queue`.
        All state should live inside the strategy instance or in the portfolio.
        """
        ...
