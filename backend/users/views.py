from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from trading.models import Wallet, Holding, Order, TradeLog
from ai_engine.models import AIInsight
from decimal import Decimal


@api_view(['GET'])
@permission_classes([AllowAny])
def test_api(request):
    return Response({"message": "Backend is working"})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({
            "message": "Login successful",
            "username": user.username,
        }, status=status.HTTP_200_OK)

    return Response({
        "error": "Invalid username or password"
    }, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({
        "message": "Logout successful"
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def me_view(request):
    if request.user.is_authenticated:
        return Response({
            "authenticated": True,
            "username": request.user.username,
        }, status=status.HTTP_200_OK)

    return Response({
        "authenticated": False
    }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user

    wallet = Wallet.objects.filter(student=user).first()
    holdings = Holding.objects.filter(student=user).select_related("stock")
    orders = Order.objects.filter(student=user)
    trade_logs = TradeLog.objects.filter(student=user).order_by("-executed_at")[:5]
    latest_ai = AIInsight.objects.filter(user=user).order_by("-created_at").first()
    ai_count = AIInsight.objects.filter(user=user).count()

    portfolio_value = Decimal("0.00")
    holdings_count = 0

    for holding in holdings:
        portfolio_value += holding.quantity * holding.stock.current_price
        holdings_count += 1

    recent_activity = []

    for log in trade_logs:
        recent_activity.append(
            f"{log.order_type} {log.quantity} shares of {log.stock_symbol} at ₹{log.price}"
        )

    if latest_ai:
        recent_activity.append(
            f"Latest AI insight: {latest_ai.risk_profile} risk profile"
        )

    return Response({
        "name": user.username,
        "email": user.email,
        "member_since": user.created_at.strftime("%d %B %Y") if user.created_at else "",
        "last_login": user.last_login.strftime("%d %B %Y, %I:%M %p") if user.last_login else "",
        "account_type": "Student" if user.is_student else "User",

        "available_balance": str(wallet.balance) if wallet else "0.00",
        "portfolio_value": str(portfolio_value),
        "holdings_count": holdings_count,
        "total_orders": orders.count(),
        "buy_orders": orders.filter(order_type="BUY").count(),
        "sell_orders": orders.filter(order_type="SELL").count(),

        "ai_usage_count": ai_count,
        "risk_profile": latest_ai.risk_profile if latest_ai else "Not available",
        "trader_type": latest_ai.trader_type if latest_ai and latest_ai.trader_type else "Not available",
        "anomaly_detected": latest_ai.anomaly_detected if latest_ai else False,
        "ai_summary": latest_ai.summary if latest_ai and latest_ai.summary else "No AI summary available",

        "recent_activity": recent_activity[:5],
    }, status=status.HTTP_200_OK)