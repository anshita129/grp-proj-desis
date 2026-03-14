import unittest
from datetime import date

from simulation.engine.replay.cached_price_store import CachedPriceStore
from simulation.engine.replay.price_store import InMemoryPriceStore, OHLC, PriceStore


class CountingPriceStore(PriceStore):
    def __init__(self, backing: InMemoryPriceStore):
        self.backing = backing
        self.calls = 0

    def get_ohlc(self, day: date, symbols):
        self.calls += 1
        return self.backing.get_ohlc(day, symbols)

    def next_trading_day_on_or_after(self, day: date):
        return self.backing.next_trading_day_on_or_after(day)

    def trading_days(self):
        return self.backing.trading_days()

    def symbols(self):
        return self.backing.symbols()


class TestCachedPriceStore(unittest.TestCase):
    def setUp(self):
        prices = {
            date(2024, 1, 1): {"AAPL": OHLC(100, 101, 99, 100), "MSFT": OHLC(200, 201, 199, 200)},
            date(2024, 1, 2): {"AAPL": OHLC(101, 102, 100, 101), "MSFT": OHLC(201, 202, 200, 201)},
        }
        self.base = InMemoryPriceStore(prices)
        self.counting = CountingPriceStore(self.base)
        self.cached = CachedPriceStore(self.counting, maxsize=16)

    def test_caches_day_fetches(self):
        # first fetch triggers delegate
        prices1 = self.cached.get_ohlc(date(2024, 1, 1), symbols=["AAPL"])
        self.assertEqual(self.counting.calls, 1)
        # second fetch same day should not call delegate again
        prices2 = self.cached.get_ohlc(date(2024, 1, 1), symbols=["MSFT"])
        self.assertEqual(self.counting.calls, 1)
        self.assertIn("MSFT", prices2)

    def test_prefetch(self):
        self.cached.prefetch([date(2024, 1, 1)])
        self.assertEqual(self.counting.calls, 1)
        # subsequent fetch should be cached
        _ = self.cached.get_ohlc(date(2024, 1, 1), symbols=["AAPL"])
        self.assertEqual(self.counting.calls, 1)


if __name__ == "__main__":
    unittest.main()
