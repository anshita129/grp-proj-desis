import os
import django
import random
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from trading.models import Stock, Wallet, Holding, Order, TradeLog
from ai_engine.models import AIInsight

User = get_user_model()

PASSWORD = "test1234"

stocks_data = [
    ("AAPL", "Apple Inc.", "Technology", Decimal("185.00")),
    ("GOOGL", "Alphabet Inc.", "Technology", Decimal("140.00")),
    ("TSLA", "Tesla Inc.", "Automobile", Decimal("220.00")),
    ("AMZN", "Amazon Inc.", "E-Commerce", Decimal("175.00")),
    ("MSFT", "Microsoft Corp.", "Technology", Decimal("410.00")),
    ("NVDA", "NVIDIA Corp.", "Technology", Decimal("900.00")),
    ("META", "Meta Platforms", "Technology", Decimal("500.00")),
    ("NFLX", "Netflix Inc.", "Entertainment", Decimal("610.00")),
    ("JPM", "JPMorgan Chase", "Finance", Decimal("195.00")),
    ("WMT", "Walmart Inc.", "Retail", Decimal("70.00")),
]

def ensure_stocks():
    stocks = []
    for sym, name, sec, price in stocks_data:
        s, _ = Stock.objects.get_or_create(
            symbol=sym,
            defaults={
                "company_name": name,
                "sector": sec,
                "current_price": price,
            }
        )
        s.company_name = name
        s.sector = sec
        s.current_price = price
        s.save()
        stocks.append(s)
    return stocks

def create_user(i, profile):
    email = f"{profile.lower()}_{i}@test.com"
    username = f"{profile.lower()}_{i}"

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": username,
            "is_student": True,
        }
    )

    if created:
        user.set_password(PASSWORD)
        user.save()

    return user

def ensure_wallet(user, balance):
    wallet, _ = Wallet.objects.get_or_create(
        student=user,
        defaults={"balance": balance, "currency": "INR"}
    )
    wallet.balance = balance
    wallet.currency = "INR"
    wallet.save()
    return wallet

def set_holdings(user, stocks, profile):
    Holding.objects.filter(student=user).delete()

    if profile == "Conservative":
        chosen = random.sample(stocks, random.randint(4, 6))
    elif profile == "Balanced":
        chosen = random.sample(stocks, random.randint(3, 5))
    elif profile == "Aggressive":
        chosen = random.sample(stocks, random.randint(1, 3))
    else:  # Anomalous
        chosen = random.sample(stocks, random.randint(1, 2))

    for st in chosen:
        if profile == "Conservative":
            qty = random.randint(2, 8)
        elif profile == "Balanced":
            qty = random.randint(5, 15)
        elif profile == "Aggressive":
            qty = random.randint(10, 30)
        else:
            qty = random.randint(20, 50)

        avg_price = st.current_price - Decimal(random.randint(1, 20))

        Holding.objects.create(
            student=user,
            stock=st,
            quantity=qty,
            avg_buy_price=avg_price,
        )

def create_orders_and_logs(user, wallet, stocks, profile):
    Order.objects.filter(student=user).delete()

    # delete related logs safely after orders delete if cascade doesn't cover legacy rows
    TradeLog.objects.filter(student=user).delete()

    if profile == "Conservative":
        n_orders = random.randint(3, 8)
    elif profile == "Balanced":
        n_orders = random.randint(8, 18)
    elif profile == "Aggressive":
        n_orders = random.randint(20, 40)
    else:
        n_orders = random.randint(30, 60)

    for _ in range(n_orders):
        st = random.choice(stocks)

        if profile == "Conservative":
            quantity = random.randint(1, 4)
        elif profile == "Balanced":
            quantity = random.randint(2, 8)
        elif profile == "Aggressive":
            quantity = random.randint(5, 15)
        else:
            quantity = random.randint(10, 25)

        order_type = random.choice(["BUY", "SELL"])
        price = st.current_price + Decimal(random.randint(-10, 10))
        total = price * quantity

        before = wallet.balance
        if order_type == "BUY":
            after = max(Decimal("0.00"), before - total)
        else:
            after = before + total

        order = Order.objects.create(
            student=user,
            stock=st,
            order_type=order_type,
            quantity=quantity,
            price_at_order=price,
            total_value=total,
            status="EXECUTED",
            executed_at=timezone.now(),
        )

        TradeLog.objects.create(
            order=order,
            student=user,
            stock_symbol=st.symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
            total_value=total,
            wallet_balance_before=before,
            wallet_balance_after=after,
        )

        wallet.balance = after
        wallet.save()

def create_ai_label(user, profile):
    AIInsight.objects.create(
        user=user,
        risk_profile=profile,
        trader_type={
            "Conservative": "Long-term Trader",
            "Balanced": "Balanced Trader",
            "Aggressive": "Frequent Trader",
            "Anomalous": "High-Risk Trader",
        }[profile],
        anomaly_detected=(profile == "Anomalous"),
        anomaly_score=0.9 if profile == "Anomalous" else (0.6 if profile == "Aggressive" else 0.2),
        summary=f"Synthetic training sample generated for {profile} profile.",
    )

def generate_group(stocks, profile, count):
    for i in range(count):
        user = create_user(i, profile)

        if profile == "Conservative":
            start_balance = Decimal(random.randint(80000, 150000))
        elif profile == "Balanced":
            start_balance = Decimal(random.randint(50000, 120000))
        elif profile == "Aggressive":
            start_balance = Decimal(random.randint(30000, 90000))
        else:
            start_balance = Decimal(random.randint(10000, 60000))

        wallet = ensure_wallet(user, start_balance)
        set_holdings(user, stocks, profile)
        create_orders_and_logs(user, wallet, stocks, profile)
        create_ai_label(user, profile)
        print(f"Generated {profile} user: {user.email}")

def main():
    stocks = ensure_stocks()

    # total = 200 users
    generate_group(stocks, "Conservative", 50)
    generate_group(stocks, "Balanced", 50)
    generate_group(stocks, "Aggressive", 50)
    generate_group(stocks, "Anomalous", 50)

    print("Finished generating synthetic ML dataset.")

if __name__ == "__main__":
    main()