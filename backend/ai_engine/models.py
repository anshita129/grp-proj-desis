from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AIInsight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_insights")
    summary = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - AI Insight"