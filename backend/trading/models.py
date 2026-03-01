from django.db import models
from django.conf import settings

# Create your models here.
class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"



User = settings.AUTH_USER_MODEL

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.FloatField(default=100000)  # starting dummy money

    def __str__(self):
        return f"{self.user} Wallet"

class Trade(models.Model):
    TRADE_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trade_type} {self.quantity} {self.stock.symbol}"