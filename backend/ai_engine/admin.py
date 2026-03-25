from django.contrib import admin
from .models import AIInsight


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "summary",
        "created_at",
    )
    search_fields = ("user__username", "user__email", "summary")
    list_filter = ("created_at",)