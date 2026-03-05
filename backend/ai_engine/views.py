from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AIInsight
from .services import get_ai_feedback


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_feedback(request):
    # if you're using the "first user" trick, keep that logic here
    # otherwise if auth is enabled, request.user will be real

    u = request.user
    data = get_ai_feedback(u)

    # Save to DB
    AIInsight.objects.create(
        user=u,
        risk_profile=data["risk_profile"],
        trade_count_last_7_days=data["trade_count_last_7_days"],
        wallet_balance=data["wallet_balance"],
        portfolio_concentration=data["portfolio_concentration"],
        tips=data["tips"],
    )

    return Response(data)

@api_view(["GET"])
def ai_history(request):
    u = request.user
    qs = AIInsight.objects.filter(user=u).order_by("-created_at")[:20]

    data = [
        {
            "risk_profile": x.risk_profile,
            "trade_count_last_7_days": x.trade_count_last_7_days,
            "wallet_balance": float(x.wallet_balance),
            "portfolio_concentration": float(x.portfolio_concentration),
            "tips": x.tips,
            "created_at": x.created_at.isoformat(),
        }
        for x in qs
    ]
    return Response(data)