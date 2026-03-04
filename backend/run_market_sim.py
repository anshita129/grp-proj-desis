import sys
import os
from datetime import date
from rich.console import Console
from rich.table import Table

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_simulation.metrics.performance import compute_metrics
from market_simulation.replay.price_store import InMemoryPriceStore, OHLC
from market_simulation.strategy.comparison_runner import StrategyComparisonRunner
from market_simulation.replay.trade_queue import ScheduledOrder

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

class AllCashStrategy:
    name = "cash"
    def on_day(self, day, prices, portfolio, trade_queue):
        pass

def main():
    console = Console()
    console.print("[bold blue]Starting Market Simulation Example...[/bold blue]\n")

    # 1. Setup mock data
    prices = {
        date(2024, 1, 1): {"AAPL": OHLC(150, 155, 149, 152)},
        date(2024, 1, 2): {"AAPL": OHLC(152, 158, 150, 157)},
        date(2024, 1, 3): {"AAPL": OHLC(157, 160, 155, 159)},
        date(2024, 1, 4): {"AAPL": OHLC(158, 162, 156, 161)},
        date(2024, 1, 5): {"AAPL": OHLC(161, 165, 160, 164)},
    }
    store = InMemoryPriceStore(prices)
    
    # 2. ConfigureRunner
    runner = StrategyComparisonRunner(
        price_store=store,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 5),
        universe=["AAPL"],
        initial_cash=10000.0,
    )
    
    # 3. Define Strategies to compare
    strategies = [
        BuyHoldStrategy(qty=50), # Buying 50 shares of AAPL
        AllCashStrategy()        # Holding cash
    ]
    
    # 4. Run Simulation
    console.print("[yellow]Running strategies: Buy & Hold (50 AAPL) vs All Cash[/yellow]")
    results = runner.run(strategies)
    console.print("[green]Simulation Complete![/green]\n")
    
    # 5. Display Results
    table = Table(title="Strategy Comparison Results")
    table.add_column("Strategy Name", justify="left", style="cyan")
    table.add_column("Final Equity", justify="right", style="magenta")
    table.add_column("Cumulative Return", justify="right", style="green")
    table.add_column("Max Drawdown", justify="right", style="red")

    for name, result in results.items():
        final_equity = result.equity_curve[-1][1]
        metrics = result.metrics
        table.add_row(
            name,
            f"${final_equity:,.2f}",
            f"{metrics.cumulative_return * 100:.2f}%",
            f"{metrics.max_drawdown * 100:.2f}%"
        )
    
    console.print(table)
    
    dashboard_data = StrategyComparisonRunner.dashboard_payload(results)
    console.print("\n[dim]Generated Dashboard Payload Keys:[/dim] " + ", ".join(dashboard_data.keys()))


if __name__ == "__main__":
    main()
