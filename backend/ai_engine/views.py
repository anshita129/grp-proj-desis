from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import AIInsight
from .serializers import AIInsightSerializer
from .services import get_rule_based_feedback, get_ml_prediction
from .llm_service import get_chatbot_reply


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

    try:
        ml_label = get_ml_prediction(user)
        ml_data = {
            "ml_available": True,
            "trader_type": ml_label,
            "is_anomaly": ml_label == "Anomalous",
            "anomaly_score": 0.9 if ml_label == "Anomalous" else 0.2,
        }
    except Exception as e:
        print("ML error:", e)
        ml_data = {
            "ml_available": False,
            "trader_type": None,
            "is_anomaly": False,
            "anomaly_score": None,
        }

    final_tips = list(rule_data.get("tips", []))

    if ml_data.get("ml_available"):
        final_tips.append(f"ML trader type detected: {ml_data['trader_type']}.")
        if ml_data.get("is_anomaly"):
            final_tips.append("Unusual behavior detected. Review your recent trades carefully.")
    else:
        final_tips.append("ML analysis is currently unavailable. Showing rule-based feedback only.")

    summary = " | ".join(final_tips)

    final_risk = (
        ml_data.get("trader_type")
        if ml_data.get("ml_available")
        else rule_data.get("risk_profile")
    )

    try:
        insight = AIInsight.objects.create(
            user=user,
            risk_profile=final_risk,
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
            "risk_profile": final_risk,
            "rule_based": rule_data,
            "ml_based": ml_data,
            "final_tips": final_tips,
            "insight_id": insight.id,
        },
        status=status.HTTP_200_OK
    )


@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({"message": "CSRF cookie set"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_history(request):
    qs = AIInsight.objects.filter(user=request.user).order_by("-created_at")
    ser = AIInsightSerializer(qs, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    user = request.user
    message = request.data.get("message", "").strip()

    if not message:
        return Response(
            {"error": "Message is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        rule_data = get_rule_based_feedback(user)

        try:
            ml_label = get_ml_prediction(user)
            ml_data = {
                "ml_available": True,
                "trader_type": ml_label,
                "is_anomaly": ml_label == "Anomalous",
                "anomaly_score": 0.9 if ml_label == "Anomalous" else 0.2,
            }
        except Exception as e:
            print("ML error:", e)
            ml_data = {
                "ml_available": False,
                "trader_type": None,
                "is_anomaly": False,
                "anomaly_score": None,
            }

        final_tips = list(rule_data.get("tips", []))

        if ml_data.get("ml_available"):
            if ml_data.get("trader_type"):
                final_tips.append(f"ML trader type detected: {ml_data['trader_type']}.")
            if ml_data.get("is_anomaly"):
                final_tips.append("Unusual behavior detected. Review your recent trades carefully.")
        else:
            final_tips.append("ML analysis is currently unavailable.")

        final_risk = (
            ml_data.get("trader_type")
            if ml_data.get("ml_available")
            else rule_data.get("risk_profile")
        )

        context = {
            "user": user,
            "username": user.username,
            "risk_profile": final_risk,
            "rule_based": rule_data,
            "ml_based": ml_data,
            "final_tips": final_tips,
            "user_message": message,
        }

        reply = get_chatbot_reply(context)

        return Response(
            {
                "reply": reply,
                "context_summary": {
                    "risk_profile": final_risk,
                    "trader_type": ml_data.get("trader_type") if ml_data.get("ml_available") else None,
                    "anomaly_detected": ml_data.get("is_anomaly") if ml_data.get("ml_available") else None,
                }
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": f"Chatbot failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )