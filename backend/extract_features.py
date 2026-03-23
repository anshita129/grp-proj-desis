import os
import django
import pandas as pd
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from trading.models import Order, TradeLog
from portfolio.models import Holding
from ai_engine.models import AIInsight

User = get_user_model()

data = []
users = User.objects.all()

for u in users:
    orders = Order.objects.filter(student=u)
    holdings = Holding.objects.filter(user=u)
    trades = TradeLog.objects.filter(student=u)

    total_orders = orders.count()
    buy_orders = orders.filter(order_type="BUY").count()
    sell_orders = orders.filter(order_type="SELL").count()
    holdings_count = holdings.count()

    total_quantity = sum(h.quantity for h in holdings) if holdings.exists() else 0

    avg_trade_size = 0
    if trades.exists():
        avg_trade_size = sum(t.total_value for t in trades) / trades.count()

    max_holding = max((h.quantity for h in holdings), default=0)
    concentration = max_holding / total_quantity if total_quantity > 0 else 0

    # new useful features
    last_7_days = timezone.now() - timedelta(days=7)
    recent_trades = trades.filter(executed_at__gte=last_7_days)

    trades_last_7_days = recent_trades.count()

    avg_recent_trade_size = 0
    if recent_trades.exists():
        avg_recent_trade_size = (
            sum(t.total_value for t in recent_trades) / recent_trades.count()
        )

    insight = AIInsight.objects.filter(user=u).order_by("-created_at").first()
    if not insight:
        continue

    data.append({
        "total_orders": total_orders,
        "buy_orders": buy_orders,
        "sell_orders": sell_orders,
        "holdings_count": holdings_count,
        "avg_trade_size": float(avg_trade_size),
        "concentration": float(concentration),
        "trades_last_7_days": trades_last_7_days,
        "avg_recent_trade_size": float(avg_recent_trade_size),
        "risk_profile": insight.risk_profile,
    })

df = pd.DataFrame(data)
df.to_csv("ml_dataset.csv", index=False)

print("Dataset created: ml_dataset.csv")
print(df.head())
print("Shape:", df.shape)