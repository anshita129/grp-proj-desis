"""Lightweight in-process event bus scoped per simulation.

Provides simple pub/sub for snapshot and audit events without introducing
external dependencies. The bus is intentionally minimal and synchronous.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Callable, DefaultDict, Dict, List, TypeVar, Generic, Any

Event = TypeVar("Event")


class EventBus(Generic[Event]):
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Event], None]) -> None:
        """Register a handler for a topic."""
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, event: Event) -> None:
        """Synchronously deliver the event to all subscribers of the topic."""
        for handler in self._subscribers.get(topic, []):
            handler(event)


@dataclass
class ValuationSnapshotEvent:
    sim_id: str
    date: date
    nav: float
    cash: float
    positions: Dict[str, Any]


@dataclass
class AuditEvent:
    sim_id: str
    date: date
    message: str
    payload: Dict[str, Any]
