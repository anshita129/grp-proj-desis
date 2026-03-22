from trading.models import Stock, DailyStockPrice, TradeLog, Holding
from django.utils import timezone  # ← ADD THIS
from datetime import timedelta, date 
from collections import defaultdict
from django.db.models import Sum, Count, Max, Avg


def get_portfolio_summary(user):
    holdings = Holding.objects.filter(student=user).select_related('stock')

    total_value = 0
    invested_amount = 0

    for h in holdings:
        current_value = h.quantity * h.stock.current_price
        invested_value = h.quantity * h.avg_buy_price

        total_value += current_value
        invested_amount += invested_value

    profit_loss = total_value - invested_amount

    return_percent = (
        (profit_loss / invested_amount) * 100
        if invested_amount > 0 else 0
    )

    return {
        "total_value": round(total_value, 2),
        "invested_amount": invested_amount,
        "profit_loss": round(profit_loss, 2),
        "return_percent": round(return_percent, 2),
    }


def get_holdings_details(user):
    holdings = Holding.objects.filter(student=user)
    from django.utils import timezone
    from datetime import timedelta

    data = []

    for h in holdings:
        current_price = h.stock.current_price
        invested_value = h.quantity * h.avg_buy_price
        current_value = h.quantity * current_price
        profit_loss = current_value - invested_value

        # 30 day average
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        prices = DailyStockPrice.objects.filter(
            stock=h.stock,
            date__gte=thirty_days_ago
        ).values_list('close_price', flat=True)

        avg_30 = sum(prices) / len(prices) if prices else None
        above_trend = current_price > avg_30 if avg_30 else None

        data.append({
            "symbol": h.stock.symbol,
            "quantity": h.quantity,
            "avg_buy_price": h.avg_buy_price,
            "current_price": float(current_price),
            "invested_value": invested_value,
            "current_value": current_value,
            "profit_loss": profit_loss,
            "avg_30_day": round(float(avg_30), 2) if avg_30 else None,
            "above_trend": above_trend
        })

    return data

def get_sector_allocation(user):
    holdings = Holding.objects.filter(student=user)

    sector_values = {}
    total_value = 0

    for h in holdings:
        sector = h.stock.sector or "Unknown"
        value = h.quantity * h.stock.current_price

        sector_values[sector] = sector_values.get(sector, 0) + value
        total_value += value

    allocation = []

    for sector, value in sector_values.items():
        percent = (value / total_value) * 100 if total_value > 0 else 0

        allocation.append({
            "sector": sector,
            "value": value,
            "percent": percent,
        })

    return allocation

def get_stock_allocation(user):
    holdings = Holding.objects.filter(student=user)

    stock_values = {}
    total_value = 0

    for h in holdings:
        symbol = h.stock.symbol
        value = h.quantity * h.stock.current_price

        stock_values[symbol] = stock_values.get(symbol, 0) + value
        total_value += value

    allocation = []

    for symbol, value in stock_values.items():
        percent = (value / total_value) * 100 if total_value > 0 else 0

        allocation.append({
            "symbol": symbol,
            "value": value,
            "percent": percent,
        })

    return allocation

def get_top_gainers_losers(user, limit=3):
    holdings = Holding.objects.filter(student=user)

    performance = []

    for h in holdings:
        avg_price = h.avg_buy_price
        current_price = h.stock.current_price

        profit_loss = (current_price - avg_price) * h.quantity

        return_percent = (
            (current_price - avg_price) / avg_price * 100
            if avg_price > 0 else 0
        )

        performance.append({
            "symbol": h.stock.symbol,
            "quantity": h.quantity,
            "avg_buy_price": avg_price,
            "current_price": current_price,
            "profit_loss": profit_loss,
            "return_percent": return_percent,
        })

    # 🔼 Sort descending → gainers
    sorted_perf = sorted(
        performance,
        key=lambda x: x["return_percent"],
        reverse=True
    )

    top_gainers = sorted_perf[:limit]

    # 🔽 Sort ascending → losers
    top_losers = sorted_perf[-limit:]
    top_losers = sorted(performance, key=lambda x: x["return_percent"])[:limit]

    return {
        "top_gainers": top_gainers,
        "top_losers": top_losers
    }

def get_portfolio_price_history(user):
    """30-day charts for user's stocks only"""
    holdings_symbols = Holding.objects.filter(
        student=user
    ).values_list('stock__symbol', flat=True).distinct()
    
    history = {}
    for symbol in holdings_symbols:
        try:
            history[symbol] = get_30_day_price_history(symbol)
        except:
            history[symbol] = []
    return history

def get_30_day_price_history(stock_symbol):
    """Single stock 30-day data"""
    stock = Stock.objects.get(symbol=stock_symbol)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    prices = stock.daily_prices.filter(
        date__gte=thirty_days_ago
    ).values('date', 'close_price').order_by('date')
    
    return list(prices)

def get_last_trade_per_stock(user):
    """Last trade info per stock"""
    trades = TradeLog.objects.filter(
        student=user
    ).order_by('stock_symbol', '-executed_at')
    
    last_trades = {}
    seen_symbols = set()
    
    for trade in trades:
        symbol = trade.stock_symbol
        if symbol not in seen_symbols:
            last_trades[symbol] = {
                'date': trade.executed_at.strftime('%Y-%m-%d'),
                'type': trade.order_type,
                'quantity': trade.quantity,
                'price': float(trade.price)
            }
            seen_symbols.add(symbol)
    
    return last_trades


def get_trading_behavior(user):
    """Trade history, spending patterns, frequency, buy/sell ratio"""
    
    # Get 90 days of trades
    three_months_ago = timezone.now() - timedelta(days=90)
    trades = TradeLog.objects.filter(
        student=user,
        executed_at__gte=three_months_ago
    ).select_related('order').order_by('-executed_at')
    
    if not trades.exists():
        return {"error": "No trading history in last 90 days"}
    
    # 1. Trade History Timeline
    timeline = trades.values(
        'executed_at__date', 'order_type'
    ).annotate(
        total_value=Sum('total_value'),
        trades_count=Count('id')
    ).order_by('executed_at__date')
    
    # 2. Spending Patterns (BUY only)
    buys = trades.filter(order_type='BUY')
    daily_spending = buys.values('executed_at__date').annotate(
        spend=Sum('total_value')
    )
    total_spent = sum(item['spend'] for item in daily_spending)
    avg_daily_spend = total_spent / len(daily_spending) if daily_spending else 0
    
    # 3. Trading Frequency
    trading_days = trades.values('executed_at__date').distinct().count()
    total_trades = trades.count()
    avg_trades_per_day = total_trades / trading_days if trading_days else 0
    
    # 4. Buy vs Sell Ratio
    buy_count = buys.count()
    sell_count = trades.filter(order_type='SELL').count()
    buy_sell_ratio = f"{buy_count}:{sell_count}"
    
    # 5. Stock-wise activity
    stock_activity = trades.values('stock_symbol').annotate(
        trades=Count('id'),
        total_volume=Sum('total_value'),
        last_trade=Max('executed_at')
    ).order_by('-trades')
    
    return {
        "timeline": list(timeline),
        "spending_patterns": {
            "total_spent": float(total_spent),
            "avg_daily_spend": round(float(avg_daily_spend), 2),
            "busiest_day": dict(daily_spending.order_by('-spend').first()) if daily_spending else None
        },
        "trading_frequency": {
            "total_trades": total_trades,
            "trading_days": trading_days,
            "avg_trades_per_day": round(avg_trades_per_day, 2),
            "most_active_stock": stock_activity[0] if stock_activity else None
        },
        "buy_sell_ratio": buy_sell_ratio,
        "stock_activity": list(stock_activity)
    }

from django.db.models import Count, Q, F
from trading.models import Order

def get_order_analytics(user):
    """Order success rate, pending orders, cancellation patterns"""
    all_orders = Order.objects.filter(student=user)
    
    metrics = {
        'total_orders': all_orders.count(),
        'status_breakdown': dict(
            all_orders.values('status')
            .annotate(count=Count('status'))
            .values_list('status', 'count')
        ),
        'success_rate': 0,
        'cancellation_rate': 0,
        'pending_limit_orders': [],
        'avg_time_to_execution': None
    }
    
    executed = all_orders.filter(status=Order.Status.EXECUTED).count()
    cancelled = all_orders.filter(status=Order.Status.CANCELLED).count()
    total = metrics['total_orders']
    
    if total > 0:
        metrics['success_rate'] = round((executed / total) * 100, 1)
        metrics['cancellation_rate'] = round((cancelled / total) * 100, 1)
    
    # Pending orders details
    pending = all_orders.filter(status=Order.Status.PENDING).select_related('stock')
    metrics['pending_limit_orders'] = [{
        'id': str(o.id),
        'symbol': o.stock.symbol,
        'type': o.order_type,
        'quantity': o.quantity,
        'price': float(o.price_at_order),
        'days_pending': (timezone.now() - o.created_at).days,
        'created': o.created_at.isoformat()
    } for o in pending]
    
    # Avg execution time
    executed_orders = all_orders.filter(status=Order.Status.EXECUTED)
    if executed_orders.exists():
        avg_time = executed_orders.aggregate(
            avg_time=Avg(F('executed_at') - F('created_at'))
        )['avg_time']
        metrics['avg_time_to_execution'] = str(avg_time) if avg_time else None
    
    return metrics

def get_portfolio_total_value_history(user, days=30):
    """
    Returns daily TOTAL portfolio value for last N days
    Format: [{"date": "2026-03-04", "total_value": 25592.50}, ...]
    """
    from datetime import timedelta, date
    from django.utils import timezone
    from django.db.models import Sum, F
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get holdings snapshot
    holdings = Holding.objects.filter(
        student=user,
        quantity__gt=0
    ).select_related('stock').values(
        'stock_id', 
        'quantity'
    )
    
    # Get daily prices for all holding stocks
    prices = DailyStockPrice.objects.filter(
        stock_id__in=[h['stock_id'] for h in holdings],
        date__range=[start_date, end_date]
    ).values('date', 'stock_id', 'close_price')
    
    # Build daily total values
    daily_totals = {}
    for price in prices:
        date_str = price['date'].strftime('%Y-%m-%d')
        if date_str not in daily_totals:
            daily_totals[date_str] = {}
        daily_totals[date_str][price['stock_id']] = price['close_price']
    
    # Calculate portfolio value each day
    history = []
    for day in range(days + 1):
        target_date = end_date - timedelta(days=day)
        date_str = target_date.strftime('%Y-%m-%d')
        
        daily_value = 0
        for holding in holdings:
            stock_id = holding['stock_id']
            price = daily_totals.get(date_str, {}).get(stock_id)
            if price:
                daily_value += holding['quantity'] * price
        
        history.append({
            'date': date_str,
            'total_value': round(daily_value, 2)
        })
    
    return sorted(history, key=lambda x: x['date'])


def get_risk_score(user):
    """
    Scores portfolio risk 0-100 based on:
    - Concentration (single stock > 40% = high risk)
    - Sector exposure (single sector > 60% = high risk)
    - Volatility (P&L swings)
    - Over-trading behavior
    """
    holdings = Holding.objects.filter(student=user).select_related('stock')
    if not holdings.exists():
        return {"score": 0, "level": "Unknown", "flags": []}

    total_value = sum(h.quantity * h.stock.current_price for h in holdings)
    if total_value == 0:
        return {"score": 0, "level": "Unknown", "flags": []}

    score = 0
    flags = []

    # 1. Concentration Risk — single stock
    for h in holdings:
        stock_value = h.quantity * h.stock.current_price
        percent = (stock_value / total_value) * 100
        if percent > 60:
            score += 40
            flags.append({
                "type": "CONCENTRATION",
                "severity": "HIGH",
                "message": f"{h.stock.symbol} is {round(percent, 1)}% of your portfolio — very concentrated!"
            })
        elif percent > 40:
            score += 20
            flags.append({
                "type": "CONCENTRATION",
                "severity": "MEDIUM",
                "message": f"{h.stock.symbol} is {round(percent, 1)}% of your portfolio — consider diversifying"
            })

    # 2. Sector Exposure Risk
    sector_values = {}
    for h in holdings:
        sector = h.stock.sector or "Unknown"
        sector_values[sector] = sector_values.get(sector, 0) + (h.quantity * h.stock.current_price)

    for sector, value in sector_values.items():
        percent = (value / total_value) * 100
        if percent > 70:
            score += 30
            flags.append({
                "type": "SECTOR_EXPOSURE",
                "severity": "HIGH",
                "message": f"{round(percent, 1)}% in {sector} sector — dangerously concentrated!"
            })
        elif percent > 50:
            score += 15
            flags.append({
                "type": "SECTOR_EXPOSURE",
                "severity": "MEDIUM",
                "message": f"{round(percent, 1)}% in {sector} sector — consider adding other sectors"
            })

    # 3. Number of stocks (< 3 = risky)
    if holdings.count() < 3:
        score += 20
        flags.append({
            "type": "LOW_DIVERSIFICATION",
            "severity": "MEDIUM",
            "message": f"Only {holdings.count()} stock(s) in portfolio — low diversification"
        })

    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "flags": flags
    }

def get_diversification_index(user):
    """
    Returns a diversification score 0-100
    Based on number of sectors, number of stocks, and balance
    """
    holdings = Holding.objects.filter(student=user).select_related('stock')
    if not holdings.exists():
        return {"score": 0, "grade": "F", "message": "No holdings found"}

    total_value = sum(h.quantity * h.stock.current_price for h in holdings)
    num_stocks = holdings.count()

    sector_values = {}
    for h in holdings:
        sector = h.stock.sector or "Unknown"
        sector_values[sector] = sector_values.get(sector, 0) + (h.quantity * h.stock.current_price)

    num_sectors = len(sector_values)

    # Stock diversity score (max 40 points)
    stock_score = min(num_stocks * 10, 40)

    # Sector diversity score (max 40 points)
    sector_score = min(num_sectors * 15, 40)

    # Balance score — penalize if one sector > 60% (max 20 points)
    max_sector_percent = max((v / total_value) * 100 for v in sector_values.values())
    if max_sector_percent < 40:
        balance_score = 20
    elif max_sector_percent < 60:
        balance_score = 10
    else:
        balance_score = 0

    total_score = stock_score + sector_score + balance_score

    if total_score >= 80:
        grade = "A"
        message = "Well diversified portfolio!"
    elif total_score >= 60:
        grade = "B"
        message = "Decent diversification, room to improve"
    elif total_score >= 40:
        grade = "C"
        message = "Moderate risk — add more sectors"
    else:
        grade = "D"
        message = "Poorly diversified — high concentration risk"

    return {
        "score": total_score,
        "grade": grade,
        "message": message,
        "num_stocks": num_stocks,
        "num_sectors": num_sectors,
        "dominant_sector": max(sector_values, key=sector_values.get),
        "dominant_sector_percent": round(max_sector_percent, 1)
    }

def get_behavioral_flags(user):
    """
    Detects emotional/risky trading patterns:
    - Panic selling (multiple sells in one day after price drop)
    - Over-trading (too many trades in a day)
    - FOMO buying (buying after big price spike)
    - Revenge trading (buy immediately after a loss)
    """
    from django.utils import timezone
    from datetime import timedelta

    three_months_ago = timezone.now() - timedelta(days=90)
    trades = TradeLog.objects.filter(
        student=user,
        executed_at__gte=three_months_ago
    ).order_by('executed_at')

    flags = []

    if not trades.exists():
        return {"flags": [], "flag_count": 0}

    # 1. Over-trading — more than 5 trades in a single day
    from django.db.models import Count
    daily_counts = trades.values('executed_at__date').annotate(
        count=Count('id')
    ).filter(count__gt=5)

    for day in daily_counts:
        flags.append({
            "type": "OVER_TRADING",
            "severity": "MEDIUM",
            "date": str(day['executed_at__date']),
            "message": f"{day['count']} trades on {day['executed_at__date']} — possible over-trading"
        })

    # 2. Panic selling — 2+ sells in one day
    daily_sells = trades.filter(order_type='SELL').values(
        'executed_at__date'
    ).annotate(count=Count('id')).filter(count__gte=2)

    for day in daily_sells:
        flags.append({
            "type": "PANIC_SELLING",
            "severity": "HIGH",
            "date": str(day['executed_at__date']),
            "message": f"Multiple sells on {day['executed_at__date']} — possible panic selling"
        })

    # 3. Buy/Sell ratio imbalance — too many buys vs sells
    total = trades.count()
    buy_count = trades.filter(order_type='BUY').count()
    buy_ratio = (buy_count / total * 100) if total > 0 else 0

    if buy_ratio > 85:
        flags.append({
            "type": "NO_EXIT_STRATEGY",
            "severity": "MEDIUM",
            "message": f"{round(buy_ratio, 1)}% of trades are BUYs — consider having an exit strategy"
        })

    return {
        "flags": flags,
        "flag_count": len(flags)
    }