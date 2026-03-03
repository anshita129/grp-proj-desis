from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Wallet, Stock, Order, Holding, TradeLog, LimitOrder

# CUSTOM EXCEPTIONS
# These are custom error types we raise so views.py can catch them specifically
# and return the right HTTP response (400, 404, etc.)
# Without these we'd have to catch generic Exception everywhere which is messy

class InsufficientFundsError(Exception):
    pass  # raised when wallet balance < amount needed to buy

class InsufficientHoldingsError(Exception):
    pass  # raised when student tries to sell more shares than they own

class StockNotFoundError(Exception):
    pass  # raised when symbol like "XYZ" doesn't exist in our Stock table

class InvalidOrderError(Exception):
    pass  # raised when input is bad — empty, negative quantity, etc.

class OrderCancellationError(Exception):
    pass  # raised when trying to cancel an order that can't be cancelled


# VALIDATION 

def validate_order_input(symbol, quantity):
    """
    Runs before any database query.
    If this fails, we never even open a transaction — saves DB resources.
    Returns cleaned symbol (stripped + uppercased) if valid.
    """

    # Check symbol is a non-empty string
    if not symbol or not isinstance(symbol, str) or not symbol.strip():
        raise InvalidOrderError("Stock symbol cannot be empty")

    # quantity must be a whole number (int) and positive
    if not isinstance(quantity, int) or quantity <= 0:
        raise InvalidOrderError(f"Quantity must be a positive integer, got: {quantity}")

    # no one should buy 1 million shares in one order
    if quantity > 100000:
        raise InvalidOrderError("Quantity cannot exceed 1,00,000 shares per order")

    return symbol.strip().upper()


#  MARKET BUY 
def execute_buy(student, symbol: str, quantity: int, idempotency_key=None ) -> Order:
    """
    Immediately buys {quantity} shares of {symbol} at current market price.
    All steps happen inside one atomic transaction — if anything fails,
    everything is rolled back automatically.
    """

    # validate input — raises InvalidOrderError if bad
    symbol = validate_order_input(symbol, quantity)


    # open atomic transaction - any exception raised in this block will roll back all DB changes automatically(postgreSQL) 
    with transaction.atomic():

        # check for idempotent order — if idempotency_key is provided, and an order with same key exists for this student, return that instead of creating a new one. 
        # This prevents duplicate orders if client retries due to network issues. 
        # If no idempotency_key or no existing order, proceed to create a new one as usual.
        if idempotency_key:
            existing = Order.objects.filter(
                student=student,
                idempotency_key=idempotency_key
            ).first()

            if existing:
                return existing
        

        # lock the wallet row with select_for_update — prevents race conditions
        wallet = Wallet.objects.select_for_update().get(student=student)

        # fetch the stock — raise error if symbol doesn't exist
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            raise StockNotFoundError(f"Stock '{symbol}' not found")

        # calculate cost
        price       = stock.current_price       
        total_value = price * quantity          

        # check if one can afford it
        if wallet.balance < total_value:
            raise InsufficientFundsError(
                f"Need {total_value}, but wallet has {wallet.balance}"
            )

        balance_before = wallet.balance
        # create the order with PENDING status first, incase something crashes 

        if idempotency_key:
            existing = Order.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing  # return the original order, don't create a new one
            
        order = Order.objects.create(
            student=student,
            stock=stock,
            order_type=Order.OrderType.BUY,
            quantity=quantity,
            price_at_order=price,
            total_value=total_value,
            status=Order.Status.PENDING, 
            #idempotency_key=idempotency_key
        )
     
        if idempotency_key:
            order.idempotency_key = idempotency_key
            order.save(update_fields=['idempotency_key'])

        # deduct wallet balance
        wallet.balance -= total_value
        wallet.save(update_fields=['balance', 'updated_at'])

        # update holdings, get or create 
        holding, created = Holding.objects.select_for_update().get_or_create(
            student=student, stock=stock,
            defaults={'quantity': 0, 'avg_buy_price': Decimal('0')}
        )

        # recalculate weighted average buy price if previously owned 
        if not created and holding.quantity > 0:
            total_qty  = holding.quantity + quantity
            total_cost = (holding.avg_buy_price * holding.quantity) + total_value
            holding.avg_buy_price = total_cost / total_qty
        else:
            holding.avg_buy_price = price

        holding.quantity += quantity
        holding.save()

        # mark order as executed
        order.status      = Order.Status.EXECUTED
        order.executed_at = timezone.now()
        order.save(update_fields=['status', 'executed_at'])

        #  write immutable audit log
        TradeLog.objects.create(
            order=order,
            student=student,
            stock_symbol=stock.symbol,
            order_type=Order.OrderType.BUY,
            quantity=quantity,
            price=price,
            total_value=total_value,
            wallet_balance_before=balance_before,
            wallet_balance_after=wallet.balance,
        )

        return order


# MARKET SELL
def execute_sell(student, symbol: str, quantity: int, idempotency_key=None) -> Order:
    """
    Immediately sells {quantity} shares of {symbol} at current market price.
    checks holdings and credits wallet.
    """

    symbol = validate_order_input(symbol, quantity)

    with transaction.atomic():
        # check for idempotent order 
        if idempotency_key:
            existing = Order.objects.filter(
                student=student,
                idempotency_key=idempotency_key
            ).first()

            if existing:
                return existing
            
        wallet = Wallet.objects.select_for_update().get(student=student)

        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            raise StockNotFoundError(f"Stock '{symbol}' not found")

        # must own the stock and have enough quantity to sell
        try:
            holding = Holding.objects.select_for_update().get(
                student=student, stock=stock
            )
        except Holding.DoesNotExist:
            raise InsufficientHoldingsError(f"You don't own any shares of {symbol}")

        # Check they own enough to sell
        if holding.quantity < quantity:
            raise InsufficientHoldingsError(
                f"You have {holding.quantity} shares of {symbol}, cannot sell {quantity}"
            )

        # price based on current value 
        price          = stock.current_price
        total_value    = price*quantity
        balance_before = wallet.balance

        order = Order.objects.create(
            student=student, stock=stock,
            order_type=Order.OrderType.SELL,
            quantity=quantity,
            price_at_order=price,
            total_value=total_value,
            status=Order.Status.PENDING, 
            #idempotency_key=idempotency_key
        )

        if idempotency_key:
            order.idempotency_key = idempotency_key
            order.save(update_fields=['idempotency_key'])

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

# LIMIT BUY 
def place_limit_buy(student, symbol: str, quantity: int, limit_price: Decimal, idempotency_key=None) -> Order:
    """
    Places a limit buy order — only executes when price <= limit_price.
    Money is reserved upfront so student can't spend it elsewhere.
    If price is already at or below limit, executes immediately.
    Otherwise sits as PENDING.
    """

    symbol = validate_order_input(symbol, quantity)

    if limit_price <= 0:
        raise InvalidOrderError("Limit price must be greater than 0")

    with transaction.atomic():

        if idempotency_key:
            existing = Order.objects.filter(
                student=student,
                idempotency_key=idempotency_key
            ).first()

            if existing:
                return existing
        
        wallet = Wallet.objects.select_for_update().get(student=student)

        # Find the stock 
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            raise StockNotFoundError(f"Stock '{symbol}' not found")

        total_value = limit_price * quantity

        # check if sufficient balance 
        if wallet.balance < total_value:
            raise InsufficientFundsError(
                f"Need {total_value} (reserved for limit order), wallet has {wallet.balance}"
            )

        # Reserve the money
        wallet.balance -= total_value
        wallet.save(update_fields=['balance', 'updated_at'])

        # create order 

        order = Order.objects.create(
            student=student,
            stock=stock,
            order_type=Order.OrderType.BUY,
            quantity=quantity,
            price_at_order=limit_price,
            total_value=total_value,
            status=Order.Status.PENDING, 
            #idempotency_key=idempotency_key
        )

        if idempotency_key:
            order.idempotency_key = idempotency_key
            order.save(update_fields=['idempotency_key'])

        # Create a LimitOrder linked to this order, so we know it's a limit order and can check its condition later
        LimitOrder.objects.create(
            order=order,
            limit_price=limit_price
        )

        # If price already satisfies condition — execute immediately
        if stock.current_price <= limit_price:
            _execute_limit_buy(order, stock, wallet)

        return order


# LIMIT SELL 
def place_limit_sell(student, symbol: str, quantity: int, limit_price: Decimal, idempotency_key=None) -> Order:
    """
    Places a limit sell order — only executes when price >= limit_price.
    No money reserved.
    """

    symbol = validate_order_input(symbol, quantity)

    if limit_price <= 0:
        raise InvalidOrderError("Limit price must be greater than 0")

    with transaction.atomic():

        if idempotency_key:
            existing = Order.objects.filter(
                student=student,
                idempotency_key=idempotency_key
            ).first()

            if existing:
                return existing
        
        # find stock 
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            raise StockNotFoundError(f"Stock '{symbol}' not found")

        # find holding 
        try:
            holding = Holding.objects.select_for_update().get(
                student=student, stock=stock
            )
        except Holding.DoesNotExist:
            raise InsufficientHoldingsError(f"You don't own any shares of {symbol}")

        if holding.quantity < quantity:
            raise InsufficientHoldingsError(
                f"You have {holding.quantity} shares, cannot place limit sell for {quantity}"
            )

        # create Order
        order = Order.objects.create(
            student=student,
            stock=stock,
            order_type=Order.OrderType.SELL,
            quantity=quantity,
            price_at_order=limit_price,
            total_value=limit_price * quantity,
            status=Order.Status.PENDING, 
            #idempotency_key=idempotency_key
        )

        if idempotency_key:
            order.idempotency_key = idempotency_key
            order.save(update_fields=['idempotency_key'])

        # Create LimitOrder linked to this order
        LimitOrder.objects.create(
            order=order,
            limit_price=limit_price
        )

        # Check if price already satisfies condition, if so execute immediately
        wallet = Wallet.objects.select_for_update().get(student=student)
        if stock.current_price >= limit_price:
            _execute_limit_sell(order, stock, holding, wallet)

        return order


# Private helper function called  when a pending limit buy condition is met
def _execute_limit_buy(order, stock, wallet):
    """
    Internal helper — called when a pending limit buy condition is met.
    Money was already reserved when order was placed, so we just execute.
    """

    # if order is no longer pending (could have been cancelled or executed in a previous iteration of this loop), skip it
    if order.status != Order.Status.PENDING:
            return order
   
    price = stock.current_price 
    total_value = price * order.quantity

    # balance_before calculation: wallet.balance is after reservation, so add back reserved amount to get true before
    balance_before = wallet.balance + order.total_value

    # get holding 
    holding, created = Holding.objects.select_for_update().get_or_create(
        student=order.student, stock=stock,
        defaults={'quantity': 0, 'avg_buy_price': Decimal('0')}
    )

    # buy the stock 
    if not created and holding.quantity > 0:
        total_qty  = holding.quantity + order.quantity
        total_cost = (holding.avg_buy_price * holding.quantity) + total_value
        holding.avg_buy_price = total_cost / total_qty
    else:
        holding.avg_buy_price = price

    holding.quantity += order.quantity
    holding.save()

    # If stock executed below limit price, refund the difference ( as we reserved money based on limit price, not current price)
    refund = order.total_value - total_value
    if refund > 0:
        wallet.balance += refund
        wallet.save(update_fields=['balance', 'updated_at'])

    # mark as executed
    order.status      = Order.Status.EXECUTED
    order.executed_at = timezone.now()
    order.save(update_fields=['status', 'executed_at'])

    # add to log 
    TradeLog.objects.create(
        order=order, student=order.student,
        stock_symbol=stock.symbol,
        order_type=Order.OrderType.BUY,
        quantity=order.quantity, price=price,
        total_value=total_value,
        wallet_balance_before=balance_before,
        wallet_balance_after=wallet.balance,
    )


# Private helper function called  when a pending limit sell condition is met
def _execute_limit_sell(order, stock, holding, wallet):
    """
    Internal helper — called when a pending limit sell condition is met.
    """

    # if order is no longer pending (could have been cancelled or executed in a previous iteration of this loop), skip it
    if order.status != Order.Status.PENDING:
        return order
   
    # price based in current value 
    price       = stock.current_price
    total_value = price * order.quantity
    balance_before = wallet.balance

    # update holdings
    holding.quantity -= order.quantity
    if holding.quantity == 0:
        holding.delete()
    else:
        holding.save(update_fields=['quantity', 'updated_at'])

    # update wallet balance
    wallet.balance += total_value
    wallet.save(update_fields=['balance', 'updated_at'])

    # update order status
    order.status      = Order.Status.EXECUTED
    order.executed_at = timezone.now()
    order.save(update_fields=['status', 'executed_at'])

    # add to log 
    TradeLog.objects.create(
        order=order, student=order.student,
        stock_symbol=stock.symbol,
        order_type=Order.OrderType.SELL,
        quantity=order.quantity, price=price,
        total_value=total_value,
        wallet_balance_before=balance_before,
        wallet_balance_after=wallet.balance,
    )


# limit order checker 
def check_limit_orders():
    """
    Called by simulate_prices after every price update.
    Scans all PENDING limit orders and executes any whose condition is now met.
    Also auto-cancels expired limit orders.
    Returns count of orders executed this run.
    """

    # Get all PENDING limit orders with related data pre-fetched (__ foreign key) 
    pending_limits = LimitOrder.objects.filter(
        order__status=Order.Status.PENDING
    ).select_related('order__stock', 'order__student')

    # how many orders executed 
    executed = 0

    for limit_order in pending_limits:
        try:
            # Each limit order execution is its own atomic transaction so If one fails, others still process
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=limit_order.order.id)
                stock = order.stock

                # If order is no longer pending (could have been executed or cancelled in a previous iteration of this loop), skip it
                if order.status != Order.Status.PENDING:
                            continue
                

                wallet = Wallet.objects.select_for_update().get(student=order.student)
                holding = Holding.objects.select_for_update().filter(
                    student=order.student, stock=stock
                ).first()  # .first() returns None if not found 

                if order.order_type == Order.OrderType.BUY:
                    # has current price has dropped to or below limit
                    if stock.current_price <= limit_order.limit_price:
                        _execute_limit_buy(order, stock, wallet)
                        executed += 1

                elif order.order_type == Order.OrderType.SELL:
                    # has current price has risen to or above limit
                    # Also check if holding exists, in case it was sold elsewhere
                    if stock.current_price >= limit_order.limit_price and holding:
                        _execute_limit_sell(order, stock, holding, wallet)
                        executed += 1

        except Exception:
            # If one order fails, skip it and continue with the rest
            continue

    # Auto-cancel expired limit orders 
    # expires_at__lt: expires_at is less than now
    expired = LimitOrder.objects.filter(
        order__status=Order.Status.PENDING,
        expires_at__lt=timezone.now()
    ).select_related('order__student')

    # cancel all expired orders 
    for limit_order in expired:
        try:
            cancel_order(limit_order.order.student, limit_order.order.id)
        except Exception:
            continue

    return executed


# cancel orders that are pending 
def cancel_order(student, order_id) -> Order:
    """
    Cancels a PENDING order.
    For limit buy orders — refunds the reserved money back to wallet.
    Cannot cancel EXECUTED or already CANCELLED orders.
    """
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(
                id=order_id, student=student
            )
        except Order.DoesNotExist:
            raise OrderCancellationError("Order not found")

        # Only PENDING orders 
        if order.status != Order.Status.PENDING:
            raise OrderCancellationError(
                f"Cannot cancel a '{order.status}' order. Only PENDING orders can be cancelled."
            )

        # Check if this was a limit buy — if so, refund reserved money
        is_limit_buy = (
            order.order_type == Order.OrderType.BUY and
            hasattr(order, 'limitorder')  # checks if LimitOrder row exists for this order
        )

        # refund if limit buy
        if is_limit_buy:
            wallet = Wallet.objects.select_for_update().get(student=student)
            wallet.balance += order.total_value 
            wallet.save(update_fields=['balance', 'updated_at'])

        # update status to cancelled
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])

        return order