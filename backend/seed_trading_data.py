import os
import django
import random
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from trading.models import Stock, Wallet, Holding, Order, TradeLog

User = get_user_model()

stocks_data = [
    ("AAPL", "Apple Inc.", "Technology", Decimal("185.00")),
    ("GOOGL", "Alphabet Inc.", "Technology", Decimal("140.00")),
    ("TSLA", "Tesla Inc.", "Automobile", Decimal("220.00")),
    ("AMZN", "Amazon Inc.", "E-Commerce", Decimal("175.00")),
    ("MSFT", "Microsoft Corp.", "Technology", Decimal("410.00")),
]

# create stocks
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
    # update price if already exists
    s.company_name = name
    s.sector = sec
    s.current_price = price
    s.save()
    stocks.append(s)

users = User.objects.filter(email__endswith="@test.com")

for u in users:
    wallet, _ = Wallet.objects.get_or_create(
        student=u,
        defaults={"balance": Decimal("100000.00"), "currency": "INR"}
    )

    # choose 2–4 random stocks per user
    chosen = random.sample(stocks, random.randint(2, 4))

    for st in chosen:
        qty = random.randint(1, 15)
        avg_price = st.current_price - Decimal(random.randint(5, 25))

        h, _ = Holding.objects.get_or_create(
            student=u,
            stock=st,
            defaults={
                "quantity": qty,
                "avg_buy_price": avg_price,
            }
        )
        h.quantity = qty
        h.avg_buy_price = avg_price
        h.save()

        # create some orders
        for _ in range(random.randint(2, 5)):
            order_type = random.choice(["BUY", "SELL"])
            q = random.randint(1, 5)
            p = st.current_price + Decimal(random.randint(-10, 10))
            total = p * q

            order = Order.objects.create(
                student=u,
                stock=st,
                order_type=order_type,
                quantity=q,
                price_at_order=p,
                total_value=total,
                status="EXECUTED",
                executed_at=timezone.now(),
            )

            TradeLog.objects.create(
                order=order,
                student=u,
                stock_symbol=st.symbol,
                order_type=order_type,
                quantity=q,
                price=p,
                total_value=total,
                wallet_balance_before=wallet.balance,
                wallet_balance_after=max(Decimal("0.00"), wallet.balance - total if order_type == "BUY" else wallet.balance + total),
            )

    print(f"Seeded trading data for {u.email}")

print("Done.")