from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Wallet, Stock, Order, Holding, TradeLog
 
 
class InsufficientFundsError(Exception):
    pass
 
class InsufficientHoldingsError(Exception):
    pass
 
class StockNotFoundError(Exception):
    pass
 
 
def execute_buy(student, symbol: str, quantity: int) -> Order:
    """
    Execute a BUY order atomically.
    Raises InsufficientFundsError if balance is too low.
    """
    with transaction.atomic():
        # Lock wallet row — prevents concurrent double-spend
        wallet = Wallet.objects.select_for_update().get(student=student)
 
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            raise StockNotFoundError(f'Stock {symbol} not found')
 
        price       = stock.current_price
        total_value = price * quantity
 
        # Validation

        if wallet.balance < total_value:
            raise InsufficientFundsError(
                f'Need ₹{total_value}, have ₹{wallet.balance}'
            )
 
        balance_before = wallet.balance
 
        #Create Order 
        order = Order.objects.create(
            student=student, stock=stock,
            order_type=Order.OrderType.BUY,
            quantity=quantity, price_at_order=price,
            total_value=total_value,
            status=Order.Status.PENDING
        )
 
        # Deduct wallet balance

        wallet.balance -= total_value
        wallet.save(update_fields=['balance', 'updated_at'])
 
        # Update holdings
        
        holding, created = Holding.objects.select_for_update().get_or_create(
            student=student, stock=stock,
            defaults={'quantity': 0, 'avg_buy_price': Decimal('0')}
        )
 
        if not created and holding.quantity > 0:
            # Recalculate weighted average buy price
            total_qty   = holding.quantity + quantity
            total_cost  = (holding.avg_buy_price * holding.quantity) + total_value
            holding.avg_buy_price = total_cost / total_qty
        else:
            holding.avg_buy_price = price
 
        holding.quantity += quantity
        holding.save()
 
        #Finalize Order
        order.status      = Order.Status.EXECUTED
        order.executed_at = timezone.now()
        order.save(update_fields=['status', 'executed_at'])
 
        # Immutable Audit Log 
        TradeLog.objects.create(
            order=order, student=student,
            stock_symbol=stock.symbol,
            order_type=Order.OrderType.BUY,
            quantity=quantity, price=price,
            total_value=total_value,
            wallet_balance_before=balance_before,
            wallet_balance_after=wallet.balance,
        )
 
        return order   # All steps above rolled back automatically if any raise
 
 
def execute_sell(student, symbol: str, quantity: int) -> Order:
    """
    Execute a SELL order atomically.
    Raises InsufficientHoldingsError if student doesn't own enough shares.
    """
    with transaction.atomic():
        # Lock both wallet and holding row together
        wallet = Wallet.objects.select_for_update().get(student=student)
 
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            raise StockNotFoundError(f'Stock {symbol} not found')
 
        try:
            holding = Holding.objects.select_for_update().get(
                student=student, stock=stock
            )
        except Holding.DoesNotExist:
            raise InsufficientHoldingsError(f'No holdings for {symbol}')
 
        if holding.quantity < quantity:
            raise InsufficientHoldingsError(
                f'Have {holding.quantity} shares, trying to sell {quantity}'
            )
 
        price       = stock.current_price
        total_value = price * quantity
        balance_before = wallet.balance
 
        order = Order.objects.create(
            student=student, stock=stock,
            order_type=Order.OrderType.SELL,
            quantity=quantity, price_at_order=price,
            total_value=total_value,
            status=Order.Status.PENDING
        )
 
        # Credit wallet
        wallet.balance += total_value
        wallet.save(update_fields=['balance', 'updated_at'])
 
        # Reduce holdings
        holding.quantity -= quantity
        if holding.quantity == 0:
            holding.delete()
        else:
            holding.save(update_fields=['quantity', 'updated_at'])
 
        order.status      = Order.Status.EXECUTED
        order.executed_at = timezone.now()
        order.save(update_fields=['status', 'executed_at'])
 
        TradeLog.objects.create(
            order=order, student=student,
            stock_symbol=stock.symbol,
            order_type=Order.OrderType.SELL,
            quantity=quantity, price=price,
            total_value=total_value,
            wallet_balance_before=balance_before,
            wallet_balance_after=wallet.balance,
        )
 
        return order
