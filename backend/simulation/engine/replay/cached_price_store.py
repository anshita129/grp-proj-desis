"""Caching wrapper for PriceStore to reduce repeated day fetches.

Caches per-day price dictionaries (date -> {symbol: OHLC}) and serves
symbol subsets without re-querying the underlying store. Supports optional
prefetch to warm cache for a set of trading days.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional, Set
from datetime import date

from simulation.engine.replay.price_store import OHLC, PriceStore


class CachedPriceStore(PriceStore):
    def __init__(self, delegate: PriceStore, maxsize: int = 512) -> None:
        self._delegate = delegate
        self._cache: Dict[date, Dict[str, OHLC]] = {}
        self._maxsize = maxsize

    def prefetch(self, days: Iterable[date]) -> None:
        for d in days:
            self._ensure_day_cached(d)

    def get_ohlc(self, day: date, symbols: Iterable[str]) -> Dict[str, OHLC]:
        full = self._ensure_day_cached(day)
        return {s: full[s] for s in symbols if s in full}

    def _ensure_day_cached(self, day: date) -> Dict[str, OHLC]:
        if day in self._cache:
            return self._cache[day]
        syms: Set[str] = set(self._delegate.symbols()) if hasattr(self._delegate, "symbols") else set()
        # if delegate requires symbols and none provided, default to all known; otherwise fetch empty
        full = self._delegate.get_ohlc(day, tuple(sorted(syms))) if syms else self._delegate.get_ohlc(day, [])
        if len(self._cache) >= self._maxsize:
            # simple FIFO eviction: pop an arbitrary item (not LRU but small and predictable)
            self._cache.pop(next(iter(self._cache)))
        self._cache[day] = full
        return full

    def next_trading_day_on_or_after(self, day: date) -> Optional[date]:
        return self._delegate.next_trading_day_on_or_after(day)

    def trading_days(self):
        return self._delegate.trading_days()

    def symbols(self):
        # optional helper
        if hasattr(self._delegate, "symbols"):
            return self._delegate.symbols()
        return set()
