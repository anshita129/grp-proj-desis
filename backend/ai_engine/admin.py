from django.contrib import admin
from .models import AIInsight


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "risk_profile",
        "trader_type",
        "anomaly_detected",
        "anomaly_score",
        "created_at",
    )
    list_filter = ("risk_profile", "anomaly_detected", "created_at")
    search_fields = ("user__username", "risk_profile", "trader_type", "summary")
    ordering = ("-created_at",)