from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import AIInsight
from .serializers import AIInsightSerializer
from .services import get_rule_based_feedback
from .ml import predict_user_behavior


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_feedback(request):
    user = request.user

    try:
        rule_data = get_rule_based_feedback(user)
    except Exception as e:
        return Response(
            {"error": f"Rule-based feedback failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    ml_data = predict_user_behavior(user)

    final_tips = list(rule_data["tips"])

    if ml_data.get("ml_available"):
        final_tips.append(f"ML trader type detected: {ml_data['trader_type']}.")
        if ml_data.get("is_anomaly"):
            final_tips.append("Unusual behavior detected. Review your recent trades carefully.")
    else:
        final_tips.append("ML analysis is currently unavailable. Showing rule-based feedback only.")

    summary = " | ".join(final_tips)

    try:
        insight = AIInsight.objects.create(
            user=user,
            risk_profile=rule_data["risk_profile"],
            trader_type=ml_data.get("trader_type") if ml_data.get("ml_available") else None,
            anomaly_detected=ml_data.get("is_anomaly", False) if ml_data.get("ml_available") else False,
            anomaly_score=ml_data.get("anomaly_score") if ml_data.get("ml_available") else None,
            summary=summary,
        )
    except Exception as e:
        return Response(
            {
                "error": f"Insight save failed: {str(e)}",
                "rule_based": rule_data,
                "ml_based": ml_data,
                "final_tips": final_tips,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "rule_based": rule_data,
            "ml_based": ml_data,
            "final_tips": final_tips,
            "insight_id": insight.id,
        },
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_history(request):
    qs = AIInsight.objects.filter(user=request.user).order_by("-created_at")
    ser = AIInsightSerializer(qs, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)