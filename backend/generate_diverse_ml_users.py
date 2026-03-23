import os
import django
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from trading.models import Stock, Wallet, Order, TradeLog, Holding as TradingHolding
from portfolio.models import Holding as PortfolioHolding
from ai_engine.models import AIInsight

User = get_user_model()

PASSWORD = "test1234"

STOCKS = [
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
    ("BAC", "Bank of America", "Finance", Decimal("38.00")),
    ("XOM", "Exxon Mobil", "Energy", Decimal("116.00")),
]

# ----------------------------
# helpers
# ----------------------------

def rdec(a, b):
    return Decimal(str(round(random.uniform(a, b), 2)))


def ensure_stocks():
    out = []
    for sym, name, sec, price in STOCKS:
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
        out.append(s)
    return out


def get_or_create_user(email, username):
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


def reset_user_data(user):
    AIInsight.objects.filter(user=user).delete()
    TradeLog.objects.filter(student=user).delete()
    Order.objects.filter(student=user).delete()
    TradingHolding.objects.filter(student=user).delete()
    PortfolioHolding.objects.filter(user=user).delete()
    Wallet.objects.filter(student=user).delete()


def create_wallet(user, balance):
    return Wallet.objects.create(
        student=user,
        balance=Decimal(str(balance)),
        currency="INR",
    )


def create_holding_pair(user, stock, qty, avg_price):
    TradingHolding.objects.create(
        student=user,
        stock=stock,
        quantity=qty,
        avg_buy_price=avg_price,
    )
    PortfolioHolding.objects.create(
        user=user,
        stock=stock,
        quantity=qty,
        avg_buy_price=avg_price,
    )


def place_order(user, wallet, stock, order_type, qty, price, executed_at):
    total = price * qty
    before = wallet.balance

    if order_type == "BUY":
        after = max(Decimal("0.00"), before - total)
    else:
        after = before + total

    order = Order.objects.create(
        student=user,
        stock=stock,
        order_type=order_type,
        quantity=qty,
        price_at_order=price,
        total_value=total,
        status="EXECUTED",
        executed_at=executed_at,
    )

    TradeLog.objects.create(
        order=order,
        student=user,
        stock_symbol=stock.symbol,
        order_type=order_type,
        quantity=qty,
        price=price,
        total_value=total,
        wallet_balance_before=before,
        wallet_balance_after=after,
        executed_at=executed_at,
    )

    wallet.balance = after
    wallet.save()
    return order


def days_ago(n):
    return timezone.now() - timedelta(days=n)


# ----------------------------
# profile generators
# ----------------------------

def generate_conservative(user, stocks):
    reset_user_data(user)

    start_balance = random.randint(90000, 180000)
    wallet = create_wallet(user, start_balance)

    chosen = random.sample(stocks, random.randint(5, 7))
    for st in chosen:
        qty = random.randint(2, 10)
        avg_price = st.current_price - rdec(1, 15)
        create_holding_pair(user, st, qty, avg_price)

    n_orders = random.randint(3, 8)
    for _ in range(n_orders):
        st = random.choice(chosen)
        qty = random.randint(1, 3)
        price = st.current_price + rdec(-5, 5)
        order_type = random.choice(["BUY", "SELL"])
        executed_at = days_ago(random.randint(5, 45))
        place_order(user, wallet, st, order_type, qty, price, executed_at)

    AIInsight.objects.create(
        user=user,
        risk_profile="Conservative",
        trader_type="Long-term Trader",
        anomaly_detected=False,
        anomaly_score=0.10,
        summary="Synthetic conservative profile with low trading frequency and diversified holdings.",
    )


def generate_balanced(user, stocks):
    reset_user_data(user)

    start_balance = random.randint(60000, 140000)
    wallet = create_wallet(user, start_balance)

    chosen = random.sample(stocks, random.randint(3, 5))
    for st in chosen:
        qty = random.randint(5, 18)
        avg_price = st.current_price - rdec(2, 20)
        create_holding_pair(user, st, qty, avg_price)

    n_orders = random.randint(10, 22)
    for _ in range(n_orders):
        st = random.choice(chosen)
        qty = random.randint(2, 7)
        price = st.current_price + rdec(-10, 10)
        order_type = random.choice(["BUY", "SELL"])
        executed_at = days_ago(random.randint(1, 25))
        place_order(user, wallet, st, order_type, qty, price, executed_at)

    AIInsight.objects.create(
        user=user,
        risk_profile="Balanced",
        trader_type="Balanced Trader",
        anomaly_detected=False,
        anomaly_score=0.25,
        summary="Synthetic balanced profile with moderate activity and moderate diversification.",
    )


def generate_aggressive(user, stocks):
    reset_user_data(user)

    start_balance = random.randint(25000, 90000)
    wallet = create_wallet(user, start_balance)

    chosen = random.sample(stocks, random.randint(1, 3))
    for st in chosen:
        qty = random.randint(20, 60)
        avg_price = st.current_price - rdec(1, 25)
        create_holding_pair(user, st, qty, avg_price)

    n_orders = random.randint(30, 65)
    recent_bias = random.randint(15, 30)

    for i in range(n_orders):
        st = random.choice(chosen)
        qty = random.randint(5, 20)
        price = st.current_price + rdec(-15, 15)
        order_type = random.choice(["BUY", "SELL"])

        if i < recent_bias:
            executed_at = days_ago(random.randint(0, 6))
        else:
            executed_at = days_ago(random.randint(7, 30))

        place_order(user, wallet, st, order_type, qty, price, executed_at)

    AIInsight.objects.create(
        user=user,
        risk_profile="Aggressive",
        trader_type="Frequent Trader",
        anomaly_detected=False,
        anomaly_score=0.55,
        summary="Synthetic aggressive profile with high activity and concentrated positions.",
    )


def generate_anomalous(user, stocks):
    reset_user_data(user)

    start_balance = random.randint(10000, 70000)
    wallet = create_wallet(user, start_balance)

    # highly concentrated
    chosen = random.sample(stocks, 1)
    st = chosen[0]
    qty = random.randint(80, 250)
    avg_price = st.current_price - rdec(1, 30)
    create_holding_pair(user, st, qty, avg_price)

    # many erratic orders, mostly very recent
    n_orders = random.randint(45, 90)
    for i in range(n_orders):
        qty = random.randint(10, 40)
        price = st.current_price + rdec(-20, 25)
        order_type = random.choice(["BUY", "SELL"])

        if i < int(0.75 * n_orders):
            executed_at = days_ago(random.randint(0, 4))
        else:
            executed_at = days_ago(random.randint(5, 20))

        place_order(user, wallet, st, order_type, qty, price, executed_at)

    # one weird spike trade
    spike_stock = random.choice(stocks)
    place_order(
        user=user,
        wallet=wallet,
        stock=spike_stock,
        order_type="BUY",
        qty=random.randint(50, 120),
        price=spike_stock.current_price + rdec(20, 60),
        executed_at=days_ago(0),
    )

    AIInsight.objects.create(
        user=user,
        risk_profile="Anomalous",
        trader_type="High-Risk Trader",
        anomaly_detected=True,
        anomaly_score=0.92,
        summary="Synthetic anomalous profile with concentrated exposure and irregular high-volume trades.",
    )


# ----------------------------
# main generator
# ----------------------------

def generate_group(stocks, profile_name, count, start_idx=0):
    fn_map = {
        "Conservative": generate_conservative,
        "Balanced": generate_balanced,
        "Aggressive": generate_aggressive,
        "Anomalous": generate_anomalous,
    }
    fn = fn_map[profile_name]

    for i in range(start_idx, start_idx + count):
        email = f"{profile_name.lower()}_{i}@test.com"
        username = f"{profile_name.lower()}_{i}"
        user = get_or_create_user(email, username)
        fn(user, stocks)
        print(f"Generated {profile_name}: {email}")


def main():
    stocks = ensure_stocks()

    # total 1000 users
    generate_group(stocks, "Conservative", 250, 0)
    generate_group(stocks, "Balanced", 250, 0)
    generate_group(stocks, "Aggressive", 250, 0)
    generate_group(stocks, "Anomalous", 250, 0)

    print("\nFinished generating diverse synthetic users.")
    print("Login password for all generated users: test1234")


if __name__ == "__main__":
    main()