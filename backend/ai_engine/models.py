from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AIInsight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_insights")
    risk_profile = models.CharField(max_length=20)
    trader_type = models.CharField(max_length=100, blank=True, null=True)
    anomaly_detected = models.BooleanField(default=False)
    anomaly_score = models.FloatField(blank=True, null=True)
    summary = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.risk_profile}"