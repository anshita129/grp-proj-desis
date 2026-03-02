from django.test import TestCase
from users.models import User
from trading.models import Wallet, Stock, Holding, TradeLog, Order
from trading.services import execute_buy, execute_sell, InsufficientFundsError, InsufficientHoldingsError
from decimal import Decimal


class TradingTestCase(TestCase):

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