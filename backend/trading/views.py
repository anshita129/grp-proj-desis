from rest_framework.views import APIView # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework import status # type: ignore
from rest_framework.permissions import IsAuthenticated # type: ignore
from .services import execute_buy, execute_sell, InsufficientFundsError, InsufficientHoldingsError
from .models import Wallet, Holding, TradeLog, Stock
 
 
class BuyView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        symbol   = request.data.get('symbol', '').strip()
        quantity = request.data.get('quantity', 0)
 
        if not symbol or not quantity:
            return Response({"error": "symbol and quantity required"}, status=400)
 
        try:
            quantity = int(quantity)
            order = execute_buy(request.user, symbol, quantity)
            return Response({
                "status": "success",
                "order_id": str(order.id),
                "message": f"Bought {quantity} shares of {symbol}"
            }, status=201)
 
        except InsufficientFundsError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "Trade failed", "detail": str(e)}, status=500)
 
 
class SellView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        symbol   = request.data.get('symbol', '').strip()
        quantity = request.data.get('quantity', 0)
 
        try:
            quantity = int(quantity)
            order = execute_sell(request.user, symbol, quantity)
            return Response({
                "status": "success",
                "order_id": str(order.id),
                "message": f"Sold {quantity} shares of {symbol}"
            }, status=201)
 
        except InsufficientHoldingsError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "Trade failed", "detail": str(e)}, status=500)
 
 
class PortfolioView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        wallet   = Wallet.objects.get(student=request.user)
        holdings = Holding.objects.filter(student=request.user).select_related('stock')
 
        portfolio = []
        total_invested = 0
        total_current  = 0
 
        for h in holdings:
            current_val = h.stock.current_price * h.quantity
            invested    = h.avg_buy_price * h.quantity
            pnl         = current_val - invested
            portfolio.append({
                "symbol":        h.stock.symbol,
                "company":       h.stock.company_name,
                "quantity":      h.quantity,
                "avg_buy_price": float(h.avg_buy_price),
                "current_price": float(h.stock.current_price),
                "current_value": float(current_val),
                "invested":      float(invested),
                "pnl":           float(pnl),
                "pnl_pct":       round(float(pnl / invested * 100), 2) if invested else 0
            })
            total_invested += float(invested)
            total_current  += float(current_val)
 
        return Response({
            "wallet_balance": float(wallet.balance),
            "total_invested": total_invested,
            "total_current_value": total_current,
            "overall_pnl": total_current - total_invested,
            "holdings": portfolio
        })
 
 
class TradeHistoryView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        logs = TradeLog.objects.filter(
            student=request.user
        ).order_by('-executed_at')[:50]
 
        return Response([{
            "order_id":    str(l.order_id), # type: ignore
            "symbol":      l.stock_symbol,
            "type":        l.order_type,
            "quantity":    l.quantity,
            "price":       float(l.price),
            "total_value": float(l.total_value),
            "balance_after": float(l.wallet_balance_after),
            "time":        l.executed_at.isoformat()
        } for l in logs])
