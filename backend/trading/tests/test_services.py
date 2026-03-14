from threading import Thread
from django.db import transaction
from users.models import User
from trading.models import Wallet, Stock, Holding, TradeLog, Order
from trading.services import InvalidOrderError, _execute_limit_buy, execute_buy, execute_sell, InsufficientFundsError, InsufficientHoldingsError, place_limit_buy, is_market_open
from decimal import Decimal
from unittest.mock import patch
from django.test import TransactionTestCase
import uuid
from django.utils import timezone
from datetime import datetime
import pytz

class TradingTestCase(TransactionTestCase):

    def setUp(self):
        # Runs before every test — fresh user, wallet, stock each time
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.wallet = Wallet.objects.create(
            student=self.user,
            balance=Decimal('10000.00')
        )
        self.stock = Stock.objects.create(
            symbol='TCS',
            company_name='Tata Consultancy',
            sector='IT',
            current_price=Decimal('100.00')
        )
        # Patch market hours to always be OPEN during tests
        # Monday 11:00 AM IST — guaranteed market open
        ist       = pytz.timezone('Asia/Kolkata')
        fake_time = ist.localize(datetime(2025, 1, 6, 11, 0, 0))
        self.market_patcher = patch(
            'trading.services.timezone.now',
            return_value=fake_time
        )
        self.market_patcher.start()

    def tearDown(self):
        # Stop the patch after each test so it doesn't leak
        self.market_patcher.stop()


    #  BUY TESTS 
    def test_buy_deducts_wallet(self):
        execute_buy(self.user, 'TCS', 10)   # 10 × 100 = 1000
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('9000.00'))

    def test_buy_creates_holding(self):
        execute_buy(self.user, 'TCS', 5)
        h = Holding.objects.get(student=self.user, stock=self.stock)
        self.assertEqual(h.quantity, 5)
        self.assertEqual(h.avg_buy_price, Decimal('100.00'))

    def test_buy_order_status_executed(self):
        order = execute_buy(self.user, 'TCS', 3)
        self.assertEqual(order.status, Order.Status.EXECUTED)

    def test_buy_creates_tradelog(self):
        order = execute_buy(self.user, 'TCS', 2)
        log = TradeLog.objects.get(order=order)
        self.assertEqual(log.quantity, 2)
        self.assertEqual(log.wallet_balance_before, Decimal('10000.00'))
        self.assertEqual(log.wallet_balance_after, Decimal('9800.00'))

    def test_buy_insufficient_funds_raises(self):
        with self.assertRaises(InsufficientFundsError):
            execute_buy(self.user, 'TCS', 9999)  # way more than balance

    def test_buy_updates_avg_price_on_second_buy(self):
        execute_buy(self.user, 'TCS', 5)   # avg = 100
        self.stock.current_price = Decimal('200.00')
        self.stock.save()
        execute_buy(self.user, 'TCS', 5)   # avg should now be 150
        h = Holding.objects.get(student=self.user, stock=self.stock)
        self.assertEqual(h.avg_buy_price, Decimal('150.00'))
        self.assertEqual(h.quantity, 10)


    # SELL TESTS 
    def test_sell_credits_wallet(self):
        execute_buy(self.user, 'TCS', 10)
        execute_sell(self.user, 'TCS', 5)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('9500.00'))

    def test_sell_reduces_holding(self):
        execute_buy(self.user, 'TCS', 10)
        execute_sell(self.user, 'TCS', 3)
        h = Holding.objects.get(student=self.user, stock=self.stock)
        self.assertEqual(h.quantity, 7)

    def test_sell_deletes_holding_when_zero(self):
        execute_buy(self.user, 'TCS', 5)
        execute_sell(self.user, 'TCS', 5)
        exists = Holding.objects.filter(student=self.user, stock=self.stock).exists()
        self.assertFalse(exists)

    def test_sell_insufficient_holdings_raises(self):
        with self.assertRaises(InsufficientHoldingsError):
            execute_sell(self.user, 'TCS', 10)  # never bought anything


    # ACID / CRASH RECOVERY TEST 
    def test_wallet_unchanged_after_crash(self):
        from unittest.mock import patch
        balance_before = self.wallet.balance

        # Simulate crash mid-transaction — TradeLog insert fails
        with patch('trading.models.TradeLog.objects.create') as mock_log:
            mock_log.side_effect = Exception('Simulated DB crash')
            with self.assertRaises(Exception):
                execute_buy(self.user, 'TCS', 10)

        # Wallet must be exactly the same — rollback worked
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, balance_before)

    def test_no_holding_created_after_crash(self):
        from unittest.mock import patch

        with patch('trading.models.TradeLog.objects.create') as mock_log:
            mock_log.side_effect = Exception('Simulated DB crash')
            with self.assertRaises(Exception):
                execute_buy(self.user, 'TCS', 10)

        exists = Holding.objects.filter(student=self.user).exists()
        self.assertFalse(exists)
    
    # check idempotency of buy/sell operations — same idempotency key should return same order without side effects
    def test_duplicate_request_returns_same_order(self):
        key = uuid.uuid4()

        order1 = execute_buy(self.user, "TCS", 5, idempotency_key=key)
        order2 = execute_buy(self.user, "TCS", 5, idempotency_key=key)

        self.assertEqual(order1.id, order2.id)
    
    def test_duplicate_request_does_not_double_deduct_wallet(self):
        key = uuid.uuid4()

        execute_buy(self.user, "TCS", 5, idempotency_key=key)
        execute_buy(self.user, "TCS", 5, idempotency_key=key)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("9500.00"))

    # check on double clicking "Place Limit Buy" button, only one order is created and executed, not two
    def test_limit_order_not_executed_twice(self):
        import uuid
        key = uuid.uuid4()

        order = place_limit_buy(
            self.user,
            "TCS",
            5,
            Decimal("100.00"),
            idempotency_key=key
        )

        stock = self.stock
        wallet = Wallet.objects.get(student=self.user)

        with transaction.atomic():
            _execute_limit_buy(order, stock, wallet)
            _execute_limit_buy(order, stock, wallet)

        wallet.refresh_from_db()
        holding = Holding.objects.get(student=self.user, stock=self.stock)

        self.assertEqual(holding.quantity, 5)

    # test that if Holding.save() fails after wallet is deducted, the wallet deduction is rolled back to prevent money disappearing on failed trades
    def test_wallet_rollback_if_holding_save_fails(self):
        balance_before = self.wallet.balance

        with patch("trading.models.Holding.save") as mock_save:
            mock_save.side_effect = Exception("Simulated failure")

            with self.assertRaises(Exception):
                execute_buy(self.user, "TCS", 5)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, balance_before)

    
    # test for concurrency — if two buy orders for the same stock are executed at the same time, wallet balance should be correctly deducted for both without ending up with a negative balance or incorrect total deduction
    def test_concurrent_buys_do_not_corrupt_wallet(self):
        def buy():
            execute_buy(self.user, "TCS", 10)

        t1 = Thread(target=buy)
        t2 = Thread(target=buy)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.wallet.refresh_from_db()

        # total cost = 2000
        self.assertEqual(self.wallet.balance, Decimal("8000.00"))

    # limit market idempotency test, if user clicks "Place Limit Buy" multiple times with same idempotency key, only one order should be created and executed, not multiple
    def test_duplicate_limit_order_same_key(self):
        key = uuid.uuid4()

        order1 = place_limit_buy(
            self.user,
            "TCS",
            5,
            Decimal("100.00"),
            idempotency_key=key
        )

        order2 = place_limit_buy(
            self.user,
            "TCS",
            5,
            Decimal("100.00"),
            idempotency_key=key
        )

        self.assertEqual(order1.id, order2.id)

    # test that a limit buy order executes when the stock price drops to or below the limit price, and that it updates the order status to EXECUTED
    def test_limit_order_executes_when_price_drops(self):
        key = uuid.uuid4()

        # Stock initially expensive
        self.stock.current_price = Decimal("200.00")
        self.stock.save()

        order = place_limit_buy(
            self.user,
            "TCS",
            5,
            Decimal("100.00"),
            idempotency_key=key
        )

        # Should still be pending
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

        # Now simulate price drop
        self.stock.current_price = Decimal("90.00")
        self.stock.save()

        # Trigger limit checker
        from trading.services import check_limit_orders
        check_limit_orders()

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.EXECUTED)

    def replay_trades(self, student):
        wallet = Decimal("10000.00")  # match initial balance
        holdings = {}


        logs = TradeLog.objects.filter(student=student).order_by("executed_at")


        for log in logs:
            if log.order_type == Order.OrderType.BUY:
                wallet -= log.total_value
                holdings[log.stock_symbol] = holdings.get(log.stock_symbol, 0) + log.quantity


            elif log.order_type == Order.OrderType.SELL:
                wallet += log.total_value
                holdings[log.stock_symbol] = holdings.get(log.stock_symbol, 0) - log.quantity


        return wallet, holdings
   
    def test_trade_replay_consistency(self):
        execute_buy(self.user, "TCS", 5)
        execute_sell(self.user, "TCS", 2)


        actual_wallet = Wallet.objects.get(student=self.user).balance
        actual_holding = Holding.objects.get(student=self.user, stock=self.stock).quantity


        replay_wallet, replay_holdings = self.replay_trades(self.user)


        self.assertEqual(actual_wallet, replay_wallet)
        self.assertEqual(actual_holding, replay_holdings["TCS"])

    #Helper — creates a timezone-aware datetime in IST. weekday: 0=Monday, 1=Tuesday ... 5=Saturday, 6=Sunday
    def _make_ist_time(self, weekday, hour, minute):
        ist = pytz.timezone('Asia/Kolkata')
        # Start from a known Monday (2025-01-06) and offset by weekday
        base = datetime(2025, 1, 6, hour, minute, 0)
        base = base + timezone.timedelta(days=weekday)
        return ist.localize(base)
    
    # Helper to patch timezone.now() to return our fake IST time during tests
    def _patch_time(self, dt):
        return patch('trading.services.timezone.now', return_value=dt)

    #  SHOULD BE OPEN: Monday 11:00 AM IST 
    def test_market_open_during_trading_hours(self):
        fake_time = self._make_ist_time(weekday=0, hour=11, minute=0)
        with self._patch_time(fake_time):
            is_open, msg = is_market_open()
        self.assertTrue(is_open)

    # Monday 3:30 PM IST should still be open
    def test_market_open_at_exactly_1530(self):
        fake_time = self._make_ist_time(weekday=0, hour=15, minute=30)
        with self._patch_time(fake_time):
            is_open, msg = is_market_open()
        self.assertTrue(is_open)

    # SHOULD BE CLOSED 
    # Monday 9:14 AM IST — one minute before open
    def test_market_closed_at_914(self):
        fake_time = self._make_ist_time(weekday=0, hour=9, minute=14)
        with self._patch_time(fake_time):
            is_open, msg = is_market_open()
        self.assertFalse(is_open)

    # Monday 3:31 PM IST — one minute after close
    def test_market_closed_after_close(self):
        fake_time = self._make_ist_time(weekday=0, hour=15, minute=31)
        with self._patch_time(fake_time):
            is_open, msg = is_market_open()
        self.assertFalse(is_open)

    # Weekend tests — market should be closed all day Saturday and Sunday
    def test_market_closed_saturday(self):
        fake_time = self._make_ist_time(weekday=5, hour=11, minute=0)
        with self._patch_time(fake_time):
            is_open, msg = is_market_open()
        self.assertFalse(is_open)
        self.assertIn("weekend", msg.lower())

    # BUY/SELL BLOCKED OUTSIDE HOURS 
    def test_buy_blocked_outside_market_hours(self):
        fake_time = self._make_ist_time(weekday=6, hour=11, minute=0)  # Sunday
        with self._patch_time(fake_time):
            with self.assertRaises(InvalidOrderError) as ctx:
                execute_buy(self.user, 'TCS', 1)
        self.assertIn("closed", str(ctx.exception).lower())

    def test_sell_blocked_outside_market_hours(self):
        fake_time = self._make_ist_time(weekday=6, hour=11, minute=0)  # Sunday
        with self._patch_time(fake_time):
            with self.assertRaises(InvalidOrderError) as ctx:
                execute_sell(self.user, 'TCS', 1)
        self.assertIn("closed", str(ctx.exception).lower())

    def test_limit_buy_allowed_outside_market_hours(self):
        """Limit orders can be placed even when market is closed"""
        fake_time = self._make_ist_time(weekday=5, hour=10, minute=0)  # Saturday
        with self._patch_time(fake_time):
            # Should NOT raise — limit orders work 24/7
            order = place_limit_buy(self.user, 'TCS', 1, Decimal('3800'))
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_buy_works_during_market_hours(self):
        fake_time = self._make_ist_time(weekday=0, hour=10, minute=0)  # Monday 10 AM
        with self._patch_time(fake_time):
            order = execute_buy(self.user, 'TCS', 1)
        self.assertEqual(order.status, Order.Status.EXECUTED)