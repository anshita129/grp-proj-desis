"""Minimal portfolio store for simulation replay."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict

from simulation.engine.replay.price_store import OHLC


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0


@dataclass
class Portfolio:
    cash: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)

    def apply_fill(self, order, fill_price: float, trade_date: date) -> None:
        qty = order.quantity if order.side == "buy" else -order.quantity
        pos = self.positions.get(order.symbol, Position(symbol=order.symbol))

        # Update position with volume-weighted average price
        new_qty = pos.quantity + qty
        if new_qty == 0:
            avg_price = 0.0
        else:
            cost_existing = pos.quantity * pos.avg_price
            cost_new = qty * fill_price
            avg_price = (cost_existing + cost_new) / new_qty

        pos.quantity = new_qty
        pos.avg_price = avg_price
        self.positions[order.symbol] = pos

        # Update cash (buy spends cash, sell adds cash)
        self.cash -= qty * fill_price

    def mark_to_market(self, prices: Dict[str, OHLC], as_of: date) -> None:
        # No-op: valuation derived in snapshot
        return

    def snapshot(self, prices: Dict[str, OHLC]) -> Dict[str, float]:
        positions_value = 0.0
        for sym, pos in self.positions.items():
            price = prices.get(sym)
            last_close = price.close if price else 0.0
            positions_value += pos.quantity * last_close
        nav = self.cash + positions_value
        return {
            "nav": nav,
            "cash": self.cash,
            "positions_value": positions_value,
            "positions": {sym: {"qty": pos.quantity, "avg_price": pos.avg_price} for sym, pos in self.positions.items()},
        }
