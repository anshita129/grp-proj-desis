from django.contrib import admin
from .models import AIInsight

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ("user", "risk_profile", "trade_count_last_7_days", "portfolio_concentration", "created_at")
    list_filter = ("risk_profile", "created_at")
    search_fields = ("user__username",)