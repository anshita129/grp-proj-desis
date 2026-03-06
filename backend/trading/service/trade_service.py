# trading/services/trade_service.py

from django.db import transaction
from django.core.exceptions import ValidationError

from trading.models import Wallet, Stock, Trade, Holding


@transaction.atomic
def execute_buy(user, stock_id, quantity):
    stock = Stock.objects.select_for_update().get(id=stock_id)
    wallet = Wallet.objects.select_for_update().get(user=user)

    total_cost = stock.current_price * quantity

    # 🔴 Validation
    if wallet.balance < total_cost:
        raise ValidationError("Insufficient balance")

    # 💰 Deduct money
    wallet.balance -= total_cost
    wallet.save()

    # 📈 Update holdings
    holding, created = Holding.objects.get_or_create(
        user=user,
        stock=stock,
        defaults={
            "quantity": 0,
            "avg_buy_price": 0,
        },
    )

    new_total_qty = holding.quantity + quantity

    # Weighted average price
    holding.avg_buy_price = (
        (holding.quantity * holding.avg_buy_price) +
        (quantity * stock.current_price)
    ) / new_total_qty

    holding.quantity = new_total_qty
    holding.save()

    # 📝 Record trade
    Trade.objects.create(
        user=user,
        stock=stock,
        trade_type="BUY",
        quantity=quantity,
        price=stock.current_price,
    )

    return "Buy successful"

@transaction.atomic
def execute_sell(user, stock_id, quantity):
    stock = Stock.objects.select_for_update().get(id=stock_id)
    wallet = Wallet.objects.select_for_update().get(user=user)
    holding = Holding.objects.select_for_update().get(
        user=user,
        stock=stock
    )

    # 🔴 Validation
    if holding.quantity < quantity:
        raise ValidationError("Not enough shares")

    total_value = stock.current_price * quantity

    # 💰 Add money
    wallet.balance += total_value
    wallet.save()

    # 📉 Update holding
    holding.quantity -= quantity

    if holding.quantity == 0:
        holding.delete()
    else:
        holding.save()

    # 📝 Record trade
    Trade.objects.create(
        user=user,
        stock=stock,
        trade_type="SELL",
        quantity=quantity,
        price=stock.current_price,
    )

    return "Sell successful"