from django.shortcuts import render


# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

from .services import get_portfolio_summary, get_holdings_details, get_sector_allocation, get_stock_allocation, get_top_gainers_losers,get_portfolio_price_history, get_last_trade_per_stock, get_trading_behavior , get_order_analytics

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_view(request):
    user = request.user

    gain_loss = get_top_gainers_losers(user)

    return Response({
        "summary": get_portfolio_summary(user),
        "holdings": get_holdings_details(user),
        "sector_allocation": get_sector_allocation(user),
        "stock_allocation": get_stock_allocation(user),
        "top_gainers": gain_loss["top_gainers"],
        "top_losers": gain_loss["top_losers"],
        "price_history": get_portfolio_price_history(user),     # ← NEW
        "last_trades": get_last_trade_per_stock(user),
        "trading_behavior": get_trading_behavior(user), 
        "order_analytics": get_order_analytics(user),         # ← NEW

    })