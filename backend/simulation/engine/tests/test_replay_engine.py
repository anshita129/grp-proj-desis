import unittest
from datetime import date

from simulation.engine.events.bus import EventBus
from simulation.engine.portfolio.store import Portfolio
from simulation.engine.replay.engine import ReplayConfig, ReplayEngine
from simulation.engine.replay.price_store import InMemoryPriceStore, OHLC
from simulation.engine.replay.trade_queue import ScheduledOrder, TradeQueue
from simulation.engine.snapshot.manager import SnapshotManager
from pathlib import Path
import tempfile


class TestReplayEngine(unittest.TestCase):
    def setUp(self) -> None:
        prices = {
            date(2024, 1, 1): {"AAPL": OHLC(100, 101, 99, 100)},
            date(2024, 1, 2): {"AAPL": OHLC(101, 102, 100, 101)},
            date(2024, 1, 3): {"AAPL": OHLC(102, 103, 101, 102)},
        }
        self.store = InMemoryPriceStore(prices)
        self.portfolio = Portfolio(cash=1000.0)
        self.trade_queue = TradeQueue()
        self.bus = EventBus()
        self.snapshots = []
        self.bus.subscribe("snapshot", lambda ev: self.snapshots.append(ev))

    def test_step_executes_trade_at_close(self):
        cfg = ReplayConfig(
            sim_id="sim-1",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            universe=["AAPL"],
        )
        engine = ReplayEngine(cfg, self.store, self.portfolio, self.trade_queue, self.bus)
        # schedule buy on Jan 2
        self.trade_queue.add(
            ScheduledOrder(
                scheduled_date=date(2024, 1, 2),
                order_id="o1",
                symbol="AAPL",
                side="buy",
                quantity=5,
            )
        )
        engine.step()  # Jan 1
        engine.step()  # Jan 2 executes

        last_snapshot = self.snapshots[-1]
        self.assertEqual(last_snapshot.date, date(2024, 1, 2))
        # After buying 5 @ 101, cash reduces by 505
        self.assertAlmostEqual(last_snapshot.cash, 1000.0 - 505.0)
        self.assertIn("AAPL", last_snapshot.positions)
        self.assertEqual(last_snapshot.positions["AAPL"]["qty"], 5)

    def test_jump_processes_sequentially(self):
        cfg = ReplayConfig(
            sim_id="sim-2",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            universe=["AAPL"],
        )
        engine = ReplayEngine(cfg, self.store, self.portfolio, self.trade_queue, self.bus)
        engine.jump_to(date(2024, 1, 3))
        self.assertEqual(self.snapshots[-1].date, date(2024, 1, 3))

    def test_snapshot_save_and_restore(self):
        cfg = ReplayConfig(
            sim_id="sim-3",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            universe=["AAPL"],
        )
        engine = ReplayEngine(cfg, self.store, self.portfolio, self.trade_queue, self.bus)

        # run one step and snapshot
        engine.step()  # processes Jan 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            snap_path = manager.create_snapshot(engine)

            # restore into a new engine and continue
            new_bus = EventBus()
            restored_snaps = []
            new_bus.subscribe("snapshot", lambda ev: restored_snaps.append(ev))
            restored_engine = manager.load_snapshot(snap_path, price_store=self.store, event_bus=new_bus)
            restored_engine.step()  # processes next trading day (Jan 2)
            self.assertEqual(restored_snaps[-1].date, date(2024, 1, 2))


if __name__ == "__main__":
    unittest.main()
