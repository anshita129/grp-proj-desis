"""Time state management for simulations.

Provides deterministic, command-driven time progression. All components
should rely on TimeState instead of system clock.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class TimeState:
    current_date: date
    end_date: date
    jump_target: Optional[date] = None
    paused: bool = False
    finished: bool = False
    mode: str = "step"  # step | jump | run_until
    history: list[date] = field(default_factory=list)

    def now(self) -> date:
        return self.current_date

    def advance_calendar_day(self) -> None:
        if self.finished:
            return
        self.current_date = self.current_date + timedelta(days=1)
        self.history.append(self.current_date)
        if self.current_date > self.end_date:
            self.finished = True

    def set_jump_target(self, target: date) -> None:
        self.jump_target = target
        self.mode = "jump"

    def mark_finished(self) -> None:
        self.finished = True

    def reset(self, start_date: date) -> None:
        self.current_date = start_date
        self.history.clear()
        self.finished = False
        self.jump_target = None
        self.paused = False
        self.mode = "step"
