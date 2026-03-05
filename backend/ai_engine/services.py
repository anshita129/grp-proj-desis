from django.utils import timezone
from datetime import timedelta

# Import your trading/portfolio models
from trading.models import TradeLog, Wallet
from portfolio.models import Holding

def get_ai_feedback(user):
    

    now = timezone.now()
    last_7_days = now - timedelta(days=7)

    # 1) Trades in last 7 days
    #recent_trades = TradeLog.objects.filter(user=user, created_at__gte=last_7_days)
    recent_trades = TradeLog.objects.filter(student=user, executed_at__gte=last_7_days)
    trade_count_7d = recent_trades.count()

    # 2) Wallet balance (if wallet exists)
    wallet = Wallet.objects.filter(student=user).first()
    balance = float(wallet.balance) if wallet else 0.0

    # 3) Portfolio concentration (top holding %)
    holdings = Holding.objects.filter(user=user).select_related("stock")
    total_value = 0.0
    max_value = 0.0
    top_stock = None

    for h in holdings:
        # If your Stock model has "price" field, use it; otherwise treat value as quantity only
        p = getattr(h.stock, "price", 1)
        v = float(h.quantity) * float(p)
        total_value += v
        if v > max_value:
            max_value = v
            top_stock = getattr(h.stock, "symbol", str(h.stock))

    concentration = (max_value / total_value) if total_value > 0 else 0.0

    # 4) Simple risk profile
    if trade_count_7d >= 20:
        risk_profile = "Aggressive"
    elif trade_count_7d >= 8:
        risk_profile = "Balanced"
    else:
        risk_profile = "Conservative"

    # 5) Generate tips (the “AI feedback”)
    tips = []

    if trade_count_7d >= 15:
        tips.append("You are trading very frequently. Consider setting a daily trade limit so you don’t overtrade.")
    elif trade_count_7d == 0:
        tips.append("No trades in the last 7 days. Try paper trading small positions to build confidence.")

    if concentration >= 0.60:
        tips.append(f"Your portfolio is highly concentrated in {top_stock}. Consider diversifying to reduce risk.")
    elif total_value == 0:
        tips.append("You currently have no holdings. Add 1-2 test trades to start building a portfolio.")

    if balance <= 0:
        tips.append("Your wallet balance is low. Add dummy funds or reduce position sizes.")

    if not tips:
        tips.append("Your trading activity looks stable. Keep tracking your risk and position sizing.")

    return {
        "risk_profile": risk_profile,
        "trade_count_last_7_days": trade_count_7d,
        "wallet_balance": balance,
        "portfolio_concentration": round(concentration, 2),
        "tips": tips,
    }