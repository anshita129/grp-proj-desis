from datetime import timedelta
from django.utils import timezone

from trading.models import TradeLog, Order
from portfolio.models import Holding

import joblib
import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

model = joblib.load(os.path.join(BASE_DIR, "ai_model.pkl"))
le = joblib.load(os.path.join(BASE_DIR, "label_encoder.pkl"))


FEATURE_COLUMNS = [
    "total_orders",
    "buy_orders",
    "sell_orders",
    "holdings_count",
    "avg_trade_size",
    "concentration",
    "trades_last_7_days",
    "avg_recent_trade_size",
]


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


def get_ml_prediction(user):
    orders = Order.objects.filter(student=user)
    holdings = Holding.objects.filter(user=user)
    trades = TradeLog.objects.filter(student=user)

    total_orders = orders.count()
    buy_orders = orders.filter(order_type="BUY").count()
    sell_orders = orders.filter(order_type="SELL").count()
    holdings_count = holdings.count()

    total_quantity = sum(h.quantity for h in holdings) if holdings.exists() else 0

    avg_trade_size = 0.0
    if trades.exists():
        avg_trade_size = sum(safe_float(t.total_value) for t in trades) / trades.count()

    max_holding = max((h.quantity for h in holdings), default=0)
    concentration = max_holding / total_quantity if total_quantity > 0 else 0.0

    last_7_days = timezone.now() - timedelta(days=7)
    recent_trades = trades.filter(executed_at__gte=last_7_days)

    trades_last_7_days = recent_trades.count()

    avg_recent_trade_size = 0.0
    if recent_trades.exists():
        avg_recent_trade_size = (
            sum(safe_float(t.total_value) for t in recent_trades) / recent_trades.count()
        )

    x = pd.DataFrame([{
        "total_orders": total_orders,
        "buy_orders": buy_orders,
        "sell_orders": sell_orders,
        "holdings_count": holdings_count,
        "avg_trade_size": float(avg_trade_size),
        "concentration": float(concentration),
        "trades_last_7_days": trades_last_7_days,
        "avg_recent_trade_size": float(avg_recent_trade_size),
    }], columns=FEATURE_COLUMNS)

    pred = model.predict(x)
    label = le.inverse_transform(pred)[0]

    return label