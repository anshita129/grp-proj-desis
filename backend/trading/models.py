from decimal import Decimal
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"


class Wallet(models.Model):
    student  = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trading_wallet'
    )
    balance  = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("100000.00"),
        validators=[MinValueValidator(0)]
    )
    currency   = models.CharField(max_length=5, default='INR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    class OrderType(models.TextChoices):
        BUY  = 'BUY',  'Buy'
        SELL = 'SELL', 'Sell'

    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending'
        EXECUTED  = 'EXECUTED',  'Executed'
        FAILED    = 'FAILED',    'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED   = 'EXPIRED',   'Expired'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trading_orders'
    )
    stock          = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='orders')
    order_type     = models.CharField(max_length=4, choices=OrderType.choices)
    quantity       = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=12, decimal_places=2)
    total_value    = models.DecimalField(max_digits=15, decimal_places=2)
    status         = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    executed_at    = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)    
    class Meta:
        indexes = [models.Index(fields=['student', 'created_at'])]


class Holding(models.Model):
    student       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trading_holdings'   # avoids clash with portfolio.Holding
    )
    stock         = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='trading_holdings'   # avoids clash with portfolio.Holding
    )
    quantity      = models.PositiveIntegerField(default=0)
    avg_buy_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'stock')


class TradeLog(models.Model):
    order                 = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='log', db_column='order_id')
    student               = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trading_logs'
    )
    stock_symbol          = models.CharField(max_length=20)
    order_type            = models.CharField(max_length=4)
    quantity              = models.PositiveIntegerField()
    price                 = models.DecimalField(max_digits=12, decimal_places=2)
    total_value           = models.DecimalField(max_digits=15, decimal_places=2)
    wallet_balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    wallet_balance_after  = models.DecimalField(max_digits=15, decimal_places=2)
    executed_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['student', '-executed_at'])]

class LimitOrder(models.Model):
    order       = models.OneToOneField(Order, on_delete=models.CASCADE)
    limit_price = models.DecimalField(max_digits=12, decimal_places=2)
    expires_at  = models.DateTimeField(null=True, blank=True)  # auto-cancel after X days