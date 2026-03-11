"""Price store interfaces and in-memory implementation for replay.

Provides efficient date + symbol lookups and trading calendar helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Set


@dataclass(frozen=True)
class OHLC:
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class PriceStore:
    """Abstract interface for price lookup."""

    def get_ohlc(self, day: date, symbols: Iterable[str]) -> Dict[str, OHLC]:
        raise NotImplementedError

    def next_trading_day_on_or_after(self, day: date) -> Optional[date]:
        raise NotImplementedError

    def trading_days(self) -> List[date]:
        raise NotImplementedError


class InMemoryPriceStore(PriceStore):
    """Simple in-memory price store keyed by date then symbol.

    Expects data shaped as dict[date][symbol] -> OHLC.
    """

    def __init__(self, prices: Dict[date, Dict[str, OHLC]]) -> None:
        self._prices = prices
        self._days_sorted: List[date] = sorted(prices.keys())

    def get_ohlc(self, day: date, symbols: Iterable[str]) -> Dict[str, OHLC]:
        day_prices = self._prices.get(day, {})
        return {s: day_prices[s] for s in symbols if s in day_prices}

    def next_trading_day_on_or_after(self, day: date) -> Optional[date]:
        # Binary search could be used; list is small in tests.
        for d in self._days_sorted:
            if d >= day:
                return d
        return None

    def trading_days(self) -> List[date]:
        return list(self._days_sorted)

    def symbols(self) -> Set[str]:
        symbols: Set[str] = set()
        for daily in self._prices.values():
            symbols.update(daily.keys())
        return symbols
