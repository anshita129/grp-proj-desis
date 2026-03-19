from rest_framework import serializers
from .models import AIInsight


class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = [
            "id",
            "risk_profile",
            "trader_type",
            "anomaly_detected",
            "anomaly_score",
            "summary",
            "created_at",
        ]