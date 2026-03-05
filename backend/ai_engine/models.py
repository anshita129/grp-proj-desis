from django.db import models
from django.conf import settings

class AIInsight(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_insights")

    risk_profile = models.CharField(max_length=32)
    trade_count_last_7_days = models.IntegerField(default=0)
    wallet_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    portfolio_concentration = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    tips = models.JSONField(default=list)  # stores list of strings

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | {self.risk_profile} | {self.created_at}"