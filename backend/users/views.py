import hashlib
import logging
import secrets
from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from trading.models import Wallet, Holding as TradingHolding, Order, TradeLog
from ai_engine.models import AIInsight

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_api(request):
    return Response({"message": "Backend is working"})


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    return Response({"message": "CSRF cookie set"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    return Response({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_student": getattr(u, "is_student", None),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""

    if not email or not password:
        return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

    authed = authenticate(request, username=user.username, password=password)
    if not authed:
        return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

    login(request, authed)
    return Response({
        "message": "Logged in",
        "user": {
            "id": authed.id,
            "username": authed.username,
            "email": authed.email
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    email = (request.data.get("email") or "").strip().lower()
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""

    if not email or not username or not password:
        return Response({"error": "Email, username, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    if User.objects.filter(email__iexact=email).exists():
        return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username__iexact=username).exists():
        return Response({"error": "A user with this username already exists."}, status=status.HTTP_400_BAD_REQUEST)

    user = User(email=email, username=username)

    try:
        validate_password(password, user=user)
    except ValidationError as e:
        return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(password)
    user.save()

    authed = authenticate(request, username=user.username, password=password)
    if authed:
        login(request, authed)
        return Response({
            "message": "Account created and logged in",
            "user": {
                "id": authed.id,
                "username": authed.username,
                "email": authed.email
            }
        }, status=status.HTTP_201_CREATED)

    return Response({"message": "Account created successfully. Please log in."}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out"})


@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_status(request):
<<<<<<< HEAD
    google_configured = False
    try:
        from allauth.socialaccount.models import SocialApp  # type: ignore
        qs = SocialApp.objects.filter(provider="google")
        google_configured = qs.exclude(client_id__isnull=True).exclude(client_id="").exists()
    except Exception:
        google_configured = False
=======
    import os
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    google_configured = bool(client_id) and "replace_me" not in client_id and "your_google_oauth_client_id_here" not in client_id
>>>>>>> kanishka

    return Response({"google_configured": google_configured})


OTP_TTL_SECONDS = 10 * 60
OTP_MAX_ATTEMPTS = 5


def _otp_cache_key(email: str) -> str:
    return f"pwd_reset_otp:{email.lower()}"


def _hash_otp(email: str, otp: str) -> str:
    return hashlib.sha256(f"{email.lower()}::{otp}".encode("utf-8")).hexdigest()


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = (request.data.get("email") or "").strip().lower()
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()

    if not user:
        return Response({"message": "If that email exists, an OTP has been sent."})

    otp = f"{secrets.randbelow(1_000_000):06d}"
    payload = {
        "otp_hash": _hash_otp(email, otp),
        "created_at": timezone.now().isoformat(),
        "attempts": 0,
    }
    cache.set(_otp_cache_key(email), payload, timeout=OTP_TTL_SECONDS)

    try:
        sent = send_mail(
            subject="Your password reset OTP",
            message=f"Your OTP is: {otp}\n\nIt expires in 10 minutes.",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )
        if sent != 1:
            logger.warning("Password reset OTP email not sent (send_mail returned %s) for %s", sent, email)
    except Exception:
        logger.exception("Failed to send password reset OTP email for %s", email)

    return Response({"message": "If that email exists, an OTP has been sent."})


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = (request.data.get("email") or "").strip().lower()
    otp = (request.data.get("otp") or "").strip()

    if not email or not otp:
        return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

    payload = cache.get(_otp_cache_key(email))
    if not payload:
        return Response({"error": "OTP expired or not found."}, status=status.HTTP_400_BAD_REQUEST)

    attempts = int(payload.get("attempts") or 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        cache.delete(_otp_cache_key(email))
        return Response({"error": "Too many attempts. Please request a new OTP."}, status=status.HTTP_400_BAD_REQUEST)

    expected = payload.get("otp_hash")
    got = _hash_otp(email, otp)
    if not secrets.compare_digest(str(expected), str(got)):
        payload["attempts"] = attempts + 1
        cache.set(_otp_cache_key(email), payload, timeout=OTP_TTL_SECONDS)
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        cache.delete(_otp_cache_key(email))
        return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    cache.delete(_otp_cache_key(email))
    return Response({"uid": uid, "token": token})


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    uid = (request.data.get("uid") or "").strip()
    token = (request.data.get("token") or "").strip()
    new_password = request.data.get("new_password") or ""

    if not uid or not token or not new_password:
        return Response({"error": "uid, token, and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = urlsafe_base64_decode(uid).decode("utf-8")
    except Exception:
        return Response({"error": "Invalid reset details."}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user or not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid reset details."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return Response({"message": "Password updated"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user

    wallet = Wallet.objects.filter(student=user).first()
    holdings = TradingHolding.objects.filter(student=user).select_related("stock")
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
        "member_since": user.created_at.strftime("%d %B %Y") if getattr(user, "created_at", None) else "",
        "last_login": user.last_login.strftime("%d %B %Y, %I:%M %p") if user.last_login else "",
        "account_type": "Student" if getattr(user, "is_student", False) else "User",

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