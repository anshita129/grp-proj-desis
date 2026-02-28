
# Create your models here.
from django.db import models
from django.conf import settings
from trading.models import Stock

User = settings.AUTH_USER_MODEL

class Holding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    avg_buy_price = models.FloatField()

    def __str__(self):
        return f"{self.user} - {self.stock.symbol}"
