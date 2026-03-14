"""Trade queue for scheduled simulated orders."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from heapq import heappop, heappush
from typing import List, Optional


@dataclass(order=True)
class ScheduledOrder:
    scheduled_date: date
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    meta: dict = field(default_factory=dict, compare=False)


class TradeQueue:
    def __init__(self) -> None:
        self._heap: List[ScheduledOrder] = []

    def add(self, order: ScheduledOrder) -> None:
        heappush(self._heap, order)

    def pop_until(self, target_date: date) -> List[ScheduledOrder]:
        """Pop all orders scheduled on or before target_date."""
        popped: List[ScheduledOrder] = []
        while self._heap and self._heap[0].scheduled_date <= target_date:
            popped.append(heappop(self._heap))
        return popped

    def peek_next_date(self) -> Optional[date]:
        return self._heap[0].scheduled_date if self._heap else None

    def __len__(self) -> int:  # for convenience
        return len(self._heap)
