import sys
import os
import time
from datetime import date
from rich.console import Console
from rich.live import Live
from rich.table import Table

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_simulation.events.bus import EventBus
from market_simulation.portfolio.store import Portfolio
from market_simulation.replay.engine import ReplayConfig, ReplayEngine
from market_simulation.replay.price_store import InMemoryPriceStore, OHLC
from market_simulation.replay.time_state import TimeState
from market_simulation.replay.trade_queue import TradeQueue, ScheduledOrder
from market_simulation.strategy.comparison_runner import StrategyComparisonRunner

def generate_mock_data():
    # 30 days of mock AAPL data for a better simulation effect
    prices = {}
    start_price = 150.0
    for i in range(1, 31):
        d = date(2024, 1, i)
        # Add some random walk logic for realism
        import random
        change = random.uniform(-2, 2.5)
        start_price += change
        prices[d] = {"AAPL": OHLC(start_price-1, start_price+1, start_price-2, start_price)}
    return prices

class BuyHoldStrategy:
    name = "buy_hold"
    def __init__(self, qty: float = 1.0):
        self.qty = qty
        self.placed = False

    def on_day(self, day, prices, portfolio, trade_queue):
        if not self.placed:
            trade_queue.add(
                ScheduledOrder(
                    scheduled_date=day,
                    order_id=f"o-{day.isoformat()}",
                    symbol="AAPL",
                    side="buy",
                    quantity=self.qty,
                )
            )
            self.placed = True

def main():
    console = Console()
    console.print("[bold blue]Starting Background Market Simulation Worker...[/bold blue]")
    console.print("[dim]This demonstrates how the backend steps through a simulation over time and pushes live updates to the frontend via WebSockets/Events.[/dim]\n")

    prices = generate_mock_data()
    store = InMemoryPriceStore(prices)
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 30)

    # Setup the core engine components explicitly (how a background task would do it)
    bus = EventBus()
    portfolio = Portfolio(cash=10000.0)
    trade_queue = TradeQueue()
    time_state = TimeState(current_date=start_date, end_date=end_date)
    
    cfg = ReplayConfig(
        sim_id="live-demo-sim",
        start_date=start_date,
        end_date=end_date,
        universe=["AAPL"],
    )

    engine = ReplayEngine(
        config=cfg,
        price_store=store,
        portfolio=portfolio,
        trade_queue=trade_queue,
        event_bus=bus,
        time_state=time_state
    )

    strategy = BuyHoldStrategy(qty=50)

    # Listen to snapshots coming out of the engine (Simulating WebSocket to Frontend)
    frontend_received_snapshots = []
    def on_snapshot(event):
        frontend_received_snapshots.append(event)
    
    bus.subscribe("snapshot", on_snapshot)

    # Setup a Live rendering table
    table = Table(title="Live Dashboard Updates (Frontend View)")
    table.add_column("Date", style="cyan")
    table.add_column("Current NAV", justify="right", style="green")
    table.add_column("Cash Available", justify="right", style="yellow")
    table.add_column("Status", justify="center", style="magenta")

    with Live(table, refresh_per_second=4) as live:
        # Run the engine step-by-step
        while not engine.finished:
            # Inject strategy hook for the day to make it trade
            curr_date = engine.time_state.now()
            today_prices = store.get_ohlc(curr_date, ["AAPL"])
            strategy.on_day(curr_date, today_prices, portfolio, trade_queue)

            # Step the engine exactly ONE day forward
            engine.step()

            # Grab the latest update pushed to the "frontend"
            if frontend_received_snapshots:
                latest = frontend_received_snapshots[-1]
                table.add_row(
                    latest.date.isoformat(),
                    f"${latest.nav:,.2f}",
                    f"${latest.cash:,.2f}",
                    "[bold]Processing...[/bold]"
                )
            
            # Sleep to simulate background processing latency and visually show the timeline
            time.sleep(0.3)

        # Update final status
        if frontend_received_snapshots:
            latest = frontend_received_snapshots[-1]
            table.add_row(
                "✅ FINISHED",
                f"${latest.nav:,.2f}",
                f"${latest.cash:,.2f}",
                "[bold green]Complete[/bold green]"
            )

if __name__ == "__main__":
    main()
