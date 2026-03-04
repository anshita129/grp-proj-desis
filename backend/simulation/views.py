from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from pathlib import Path
import random

from market_simulation.metrics.performance import compute_metrics
from market_simulation.replay.price_store import InMemoryPriceStore, OHLC
from market_simulation.strategy.comparison_runner import StrategyComparisonRunner
from market_simulation.replay.trade_queue import ScheduledOrder, TradeQueue
from market_simulation.snapshot.manager import SnapshotManager
from market_simulation.events.bus import EventBus
from market_simulation.portfolio.store import Portfolio
from market_simulation.replay.engine import ReplayConfig, ReplayEngine
from market_simulation.replay.time_state import TimeState

WORKSPACE_DIR = Path("/tmp/sim_snapshots")
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
snapshot_manager = SnapshotManager(WORKSPACE_DIR)

class BuyHoldStrategy:
    name = "buy_hold"
    def __init__(self, qty: float = 1.0):
        self.qty = qty
        self.placed = False

    def on_day(self, day, prices, portfolio, trade_queue):
        if not self.placed:
            trade_queue.add(ScheduledOrder(scheduled_date=day, order_id=f"o-{day.isoformat()}", symbol="AAPL", side="buy", quantity=self.qty))
            self.placed = True

class AllCashStrategy:
    name = "cash"
    def on_day(self, day, prices, portfolio, trade_queue):
        pass

class RunSimulationView(APIView):
    def get(self, request):
        prices = {
            date(2024, 1, 1): {"AAPL": OHLC(150, 155, 149, 152)},
            date(2024, 1, 2): {"AAPL": OHLC(152, 158, 150, 157)},
            date(2024, 1, 3): {"AAPL": OHLC(157, 160, 155, 159)},
            date(2024, 1, 4): {"AAPL": OHLC(158, 162, 156, 161)},
            date(2024, 1, 5): {"AAPL": OHLC(161, 165, 160, 164)},
        }
        store = InMemoryPriceStore(prices)
        runner = StrategyComparisonRunner(price_store=store, start_date=date(2024, 1, 1), end_date=date(2024, 1, 5), universe=["AAPL"], initial_cash=10000.0)
        results = runner.run([BuyHoldStrategy(qty=50), AllCashStrategy()])
        return Response({"message": "Simulation ran successfully.", "data": StrategyComparisonRunner.dashboard_payload(results)}, status=status.HTTP_200_OK)

# --- NEW INTERACTIVE ENDPOINT ---

def generate_mock_data():
    prices = {}
    start_price = 150.0
    for i in range(1, 31):
        d = date(2024, 1, i)
        start_price += random.uniform(-2, 2.5)
        prices[d] = {"AAPL": OHLC(start_price-1, start_price+1, start_price-2, start_price)}
    return prices
    
STATIC_PRICES = generate_mock_data()
STATIC_STORE = InMemoryPriceStore(STATIC_PRICES)

class InteractiveSimulationView(APIView):
    def post(self, request):
        action = request.data.get("action")
        snapshot_id = request.data.get("snapshot_id")
        
        bus = EventBus()
        
        def get_snapshot_path(sid):
            for p in WORKSPACE_DIR.glob(f"*_{sid}.json.gz"):
                return p
            return None

        if action == "start":
            cfg = ReplayConfig(sim_id="interactive-sim", start_date=date(2024,1,1), end_date=date(2024,1,30), universe=["AAPL"])
            engine = ReplayEngine(
                config=cfg,
                price_store=STATIC_STORE,
                portfolio=Portfolio(cash=10000.0),
                trade_queue=TradeQueue(),
                event_bus=bus,
                time_state=TimeState(current_date=date(2024,1,1), end_date=date(2024,1,30))
            )
            
            snap_path = snapshot_manager.create_snapshot(engine)
            new_sid = snap_path.name.split('_')[-1].replace('.json.gz', '')
            
            prices_today = STATIC_STORE.get_ohlc(engine.time_state.now(), ["AAPL"])
            return Response({
                "message": "Simulation started",
                "snapshot_id": new_sid,
                "current_date": engine.time_state.now(),
                "portfolio": engine.portfolio.snapshot(prices_today)
            })
            
        elif action == "advance":
            snap_path = get_snapshot_path(snapshot_id)
            if not snap_path:
                return Response({"error": "Invalid snapshot ID"}, status=400)
                
            engine = snapshot_manager.load_snapshot(snap_path, STATIC_STORE, bus)
            
            if engine.finished:
                 return Response({"error": "Simulation already finished"}, status=400)

            # Step exactly one day forward
            engine.step()
            
            new_snap_path = snapshot_manager.create_snapshot(engine)
            new_sid = new_snap_path.name.split('_')[-1].replace('.json.gz', '')
            
            prices_today = STATIC_STORE.get_ohlc(engine.time_state.now(), ["AAPL"])
            return Response({
                "message": "Advanced 1 day",
                "snapshot_id": new_sid,
                "current_date": engine.time_state.now(),
                "portfolio": engine.portfolio.snapshot(prices_today),
                "finished": engine.finished
            })
            
        elif action == "trade":
            snap_path = get_snapshot_path(snapshot_id)
            if not snap_path:
                return Response({"error": "Invalid snapshot ID"}, status=400)
                
            engine = snapshot_manager.load_snapshot(snap_path, STATIC_STORE, bus)
            symbol = request.data.get("symbol", "AAPL")
            side = request.data.get("side", "buy")
            quantity = float(request.data.get("quantity", 0))
            
            engine.trade_queue.add(
                ScheduledOrder(
                    scheduled_date=engine.time_state.now(),
                    order_id=f"manual-{random.randint(1000,9999)}",
                    symbol=symbol,
                    side=side,
                    quantity=quantity
                )
            )
            
            new_snap_path = snapshot_manager.create_snapshot(engine)
            new_sid = new_snap_path.name.split('_')[-1].replace('.json.gz', '')
            
            prices_today = STATIC_STORE.get_ohlc(engine.time_state.now(), ["AAPL"])
            return Response({
                "message": f"Queued {side} order for {quantity} {symbol}",
                "snapshot_id": new_sid,
                "current_date": engine.time_state.now(),
                "portfolio": engine.portfolio.snapshot(prices_today)
            })
            
        return Response({"error": "Unknown action"}, status=400)
