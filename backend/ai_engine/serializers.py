from rest_framework import serializers
from .models import AIInsight


class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = [
            "id",
            "risk_profile",
            "summary",
            "created_at",
        ]