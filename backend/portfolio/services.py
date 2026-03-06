from .models import Holding

def get_portfolio_summary(user):
    holdings = Holding.objects.filter(user=user)

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
        "total_value": total_value,
        "invested_amount": invested_amount,
        "profit_loss": profit_loss,
        "return_percent": return_percent,
    }


def get_holdings_details(user):
    holdings = Holding.objects.filter(user=user)

    data = []

    for h in holdings:
        current_price = h.stock.current_price

        invested_value = h.quantity * h.avg_buy_price
        current_value = h.quantity * current_price
        profit_loss = current_value - invested_value

        data.append({
            "symbol": h.stock.symbol,
            "quantity": h.quantity,
            "avg_buy_price": h.avg_buy_price,
            "current_price": current_price,
            "invested_value": invested_value,
            "current_value": current_value,
            "profit_loss": profit_loss,
        })

    return data

def get_sector_allocation(user):
    holdings = Holding.objects.filter(user=user)

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
    holdings = Holding.objects.filter(user=user)

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
    holdings = Holding.objects.filter(user=user)

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
    top_losers.reverse()

    return {
        "top_gainers": top_gainers,
        "top_losers": top_losers
    }