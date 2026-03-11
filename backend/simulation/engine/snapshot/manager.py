"""Snapshot manager for simulation state recovery.

Provides create/load functions to avoid recomputing from the scenario start.
Snapshots are stored per-simulation in a workspace directory, separate from
live trading tables or services.
"""
from __future__ import annotations

import gzip
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

from simulation.engine.events.bus import EventBus
from simulation.engine.portfolio.store import Portfolio, Position
from simulation.engine.replay.engine import ReplayConfig, ReplayEngine
from simulation.engine.replay.price_store import PriceStore
from simulation.engine.replay.time_state import TimeState
from simulation.engine.replay.trade_queue import ScheduledOrder, TradeQueue


@dataclass
class SnapshotMeta:
    snapshot_id: str
    sim_id: str
    scenario_id: str | None
    taken_at: str  # ISO timestamp
    engine_version: str = "v1"


class SnapshotManager:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _snapshot_path(self, snapshot_id: str, taken_at: str) -> Path:
        return self.workspace / f"{taken_at}_{snapshot_id}.json.gz"

    def create_snapshot(self, engine: ReplayEngine) -> Path:
        """Serialize minimal simulation state to a compressed JSON snapshot."""
        snapshot_id = str(uuid.uuid4())
        taken_at_ts = datetime.utcnow().isoformat()
        meta = SnapshotMeta(
            snapshot_id=snapshot_id,
            sim_id=engine.config.sim_id,
            scenario_id=engine.config.scenario_id,
            taken_at=taken_at_ts,
        )

        # Serialize time state
        ts = engine.time_state
        time_state_dict = {
            "current_date": ts.current_date.isoformat(),
            "end_date": ts.end_date.isoformat(),
            "jump_target": ts.jump_target.isoformat() if ts.jump_target else None,
            "paused": ts.paused,
            "finished": ts.finished,
            "mode": ts.mode,
            "history": [d.isoformat() for d in ts.history],
        }

        # Serialize portfolio
        portfolio_dict = {
            "cash": engine.portfolio.cash,
            "positions": {
                sym: {
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                }
                for sym, pos in engine.portfolio.positions.items()
            },
        }

        # Serialize trade queue
        queue_items = [
            {
                "scheduled_date": order.scheduled_date.isoformat(),
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "meta": order.meta,
            }
            for order in sorted(engine.trade_queue._heap)
        ]

        payload: Dict[str, Any] = {
            "meta": asdict(meta),
            "config": {
                "sim_id": engine.config.sim_id,
                "scenario_id": engine.config.scenario_id,
                "start_date": engine.config.start_date.isoformat(),
                "end_date": engine.config.end_date.isoformat(),
                "universe": list(engine.config.universe),
                "strict_missing_prices": engine.config.strict_missing_prices,
            },
            "time_state": time_state_dict,
            "portfolio": portfolio_dict,
            "trade_queue": queue_items,
        }

        path = self._snapshot_path(snapshot_id, ts.current_date.isoformat())
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(payload, f)
        return path

    def load_snapshot(
        self,
        snapshot_path: Path,
        price_store: PriceStore,
        event_bus: EventBus,
    ) -> ReplayEngine:
        """Load a snapshot file and construct a ReplayEngine ready to resume."""
        with gzip.open(snapshot_path, "rt", encoding="utf-8") as f:
            data = json.load(f)

        cfg_data = data["config"]
        time_data = data["time_state"]
        portfolio_data = data["portfolio"]
        queue_items = data["trade_queue"]

        config = ReplayConfig(
            sim_id=cfg_data["sim_id"],
            scenario_id=cfg_data.get("scenario_id"),
            start_date=date.fromisoformat(cfg_data["start_date"]),
            end_date=date.fromisoformat(cfg_data["end_date"]),
            universe=cfg_data["universe"],
            strict_missing_prices=cfg_data.get("strict_missing_prices", False),
        )

        time_state = TimeState(
            current_date=date.fromisoformat(time_data["current_date"]),
            end_date=date.fromisoformat(time_data["end_date"]),
            jump_target=date.fromisoformat(time_data["jump_target"]) if time_data.get("jump_target") else None,
            paused=time_data.get("paused", False),
            finished=time_data.get("finished", False),
            mode=time_data.get("mode", "step"),
            history=[date.fromisoformat(d) for d in time_data.get("history", [])],
        )

        portfolio = Portfolio(cash=portfolio_data["cash"])
        for sym, pos in portfolio_data["positions"].items():
            portfolio.positions[sym] = Position(symbol=sym, quantity=pos["quantity"], avg_price=pos["avg_price"])

        trade_queue = TradeQueue()
        for item in queue_items:
            trade_queue.add(
                ScheduledOrder(
                    scheduled_date=date.fromisoformat(item["scheduled_date"]),
                    order_id=item["order_id"],
                    symbol=item["symbol"],
                    side=item["side"],
                    quantity=item["quantity"],
                    meta=item.get("meta", {}),
                )
            )

        engine = ReplayEngine(
            config=config,
            price_store=price_store,
            portfolio=portfolio,
            trade_queue=trade_queue,
            event_bus=event_bus,
            time_state=time_state,
        )
        return engine
