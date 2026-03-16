from django.shortcuts import render


# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from portfolio.services import get_diversification_index, get_portfolio_summary, get_holdings_details, get_sector_allocation, get_stock_allocation, get_top_gainers_losers,get_portfolio_price_history, get_last_trade_per_stock, get_trading_behavior , get_order_analytics,  get_portfolio_total_value_history ,get_risk_score,get_diversification_index, get_behavioral_flags
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class PortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        gain_loss = get_top_gainers_losers(user)

        return Response({
            "summary": get_portfolio_summary(user),
            "holdings": get_holdings_details(user),
            "sector_allocation": get_sector_allocation(user),
            "stock_allocation": get_stock_allocation(user),
            "top_gainers": gain_loss["top_gainers"],
            "top_losers": gain_loss["top_losers"],
            "price_history": get_portfolio_price_history(user),     
            "last_trades": get_last_trade_per_stock(user),
            "trading_behavior": get_trading_behavior(user), 
            "order_analytics": get_order_analytics(user),  
            "portfolio_value_history": get_portfolio_total_value_history(user),    
            "risk": get_risk_score(user),                        # ← NEW
            "diversification": get_diversification_index(user),  # ← NEW
            "behavioral_flags": get_behavioral_flags(user),  
        })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def portfolio_view(request):
#     user = request.user

#     gain_loss = get_top_gainers_losers(user)

#     return Response({
#         "summary": get_portfolio_summary(user),
#         "holdings": get_holdings_details(user),
#         "sector_allocation": get_sector_allocation(user),
#         "stock_allocation": get_stock_allocation(user),
#         "top_gainers": gain_loss["top_gainers"],
#         "top_losers": gain_loss["top_losers"],
#         "price_history": get_portfolio_price_history(user),     # ← NEW
#         "last_trades": get_last_trade_per_stock(user),
#         "trading_behavior": get_trading_behavior(user), 
#         "order_analytics": get_order_analytics(user),         # ← NEW

#     })




