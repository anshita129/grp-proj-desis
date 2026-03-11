
# Create your models here.
from django.db import models
from trading.models import Stock
from django.contrib.auth import get_user_model
User = get_user_model()


# In your portfolio view or serializer:
# from django.contrib.auth import get_user_model
# User = get_user_model()
# The following line was erroneous and removed:
# holdings = TradingHolding.objects.filter(student=request.user).select_related('stock')
User = settings.AUTH_USER_MODEL


class Holding(models.Model):
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_holdings')
    stock         = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='portfolio_holdings')
    quantity      = models.PositiveIntegerField()
    avg_buy_price = models.DecimalField(max_digits=12, decimal_places=2)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "stock")

    def __str__(self):
        return f"{self.user} - {self.stock.symbol}"

