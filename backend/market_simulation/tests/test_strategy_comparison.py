import unittest
from datetime import date

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
        # do nothing
        return


class TestStrategyComparison(unittest.TestCase):
    def setUp(self):
        prices = {
            date(2024, 1, 1): {"AAPL": OHLC(100, 101, 99, 100)},
            date(2024, 1, 2): {"AAPL": OHLC(101, 102, 100, 101)},
            date(2024, 1, 3): {"AAPL": OHLC(102, 103, 101, 102)},
        }
        self.store = InMemoryPriceStore(prices)

    def test_compare_two_strategies(self):
        runner = StrategyComparisonRunner(
            price_store=self.store,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            universe=["AAPL"],
            initial_cash=1000.0,
        )
        results = runner.run([BuyHoldStrategy(qty=5), AllCashStrategy()])
        self.assertIn("buy_hold", results)
        self.assertIn("cash", results)
        # buy_hold should have higher final NAV than cash
        self.assertGreater(results["buy_hold"].equity_curve[-1][1], results["cash"].equity_curve[-1][1])
        # metrics sanity
        m = results["buy_hold"].metrics
        self.assertGreaterEqual(m.cumulative_return, 0)


if __name__ == "__main__":
    unittest.main()
