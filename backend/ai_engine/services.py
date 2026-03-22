from datetime import timedelta
from django.utils import timezone

from trading.models import TradeLog
from portfolio.models import Holding


def safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def get_latest_wallet_balance(user):
    last_trade = TradeLog.objects.filter(student=user).order_by("-executed_at").first()
    if not last_trade:
        return 0.0
    return safe_float(getattr(last_trade, "wallet_balance_after", 0.0))


def get_rule_based_feedback(user):
    last_7_days = timezone.now() - timedelta(days=7)

    trades_last_7_days = TradeLog.objects.filter(
        student=user,
        executed_at__gte=last_7_days
    )
    holdings = Holding.objects.filter(user=user)

    trade_count_last_7_days = trades_last_7_days.count()
    wallet_balance = get_latest_wallet_balance(user)

    portfolio_value = 0.0
    max_holding_value = 0.0

    for h in holdings:
        qty = safe_float(getattr(h, "quantity", 0.0))
        avg_buy_price = safe_float(getattr(h, "avg_buy_price", 0.0))
        value = qty * avg_buy_price
        portfolio_value += value
        if value > max_holding_value:
            max_holding_value = value

    portfolio_concentration = (
        max_holding_value / portfolio_value if portfolio_value > 0 else 0.0
    )

    if trade_count_last_7_days < 5 and portfolio_concentration < 0.4:
        risk_profile = "Conservative"
    elif trade_count_last_7_days < 15 and portfolio_concentration < 0.6:
        risk_profile = "Balanced"
    else:
        risk_profile = "Aggressive"

    tips = []

    if portfolio_concentration > 0.6:
        tips.append("Your portfolio is highly concentrated. Consider diversifying into more assets.")

    if trade_count_last_7_days > 20:
        tips.append("You are trading very frequently. Try to avoid overtrading.")

    if wallet_balance < 1000:
        tips.append("Your available balance is low. Plan your next trades carefully.")

    if not tips:
        tips.append("Your current trading behavior looks stable. Keep monitoring your risk exposure.")

    return {
        "trade_count_last_7_days": trade_count_last_7_days,
        "wallet_balance": wallet_balance,
        "portfolio_concentration": portfolio_concentration,
        "risk_profile": risk_profile,
        "tips": tips,
    }