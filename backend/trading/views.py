# trading/views.py
from decimal import Decimal, InvalidOperation
from urllib import request
from rest_framework.views import APIView # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.permissions import IsAuthenticated # type: ignore
from .models import Wallet, Holding, TradeLog, Stock, Order

from .services import (
    execute_buy, execute_sell,
    place_limit_buy, place_limit_sell,
    cancel_order,
    InsufficientFundsError, InsufficientHoldingsError,
    StockNotFoundError, InvalidOrderError, OrderCancellationError
)

# checks if user is logged in before running any trading operation, otherwise returns 401 Unauthorized
class BuyView(APIView):
    permission_classes = [IsAuthenticated]
    

    # Handle HTTP POST request to buy stocks. Expects JSON body with 'symbol', 'quantity', and optional 'limit_price'.
    def post(self, request):
        symbol   = request.data.get('symbol', '').strip()
        quantity = request.data.get('quantity', 0)
        limit    = request.data.get('limit_price') 
        idempotency_key = request.data.get("idempotency_key")

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"error": "quantity must be a whole number"}, status=400)

        try:
            # depending on whether limit price is provided, call the appropriate service function to execute the buy order
            if limit:
                limit_price = Decimal(str(limit))
                order = place_limit_buy(request.user, symbol, quantity, limit_price, idempotency_key=idempotency_key)
                msg = f"Limit buy placed for {quantity} shares of {symbol} at ₹{limit_price}"
            else:
                order = execute_buy(request.user, symbol, quantity, idempotency_key=idempotency_key)
                msg = f"Bought {quantity} shares of {symbol} at market price"

            # return a success response with order details and message
            return Response({
                "status": "success",
                "order_id": str(order.id),
                "order_status": order.status,
                "message": msg
            }, status=201)

        # handle various exceptions that can occur during order processing and return appropriate error responses
        except InvalidOrderError       as e: return Response({"error": str(e)}, status=400)
        except InsufficientFundsError  as e: return Response({"error": str(e)}, status=400)
        except StockNotFoundError      as e: return Response({"error": str(e)}, status=404)
        except InvalidOperation        as e: return Response({"error": "Invalid limit price"}, status=400)
        except Exception               as e: return Response({"error": str(e)}, status=500)


# similar to BuyView but for selling stocks
class SellView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        symbol   = request.data.get('symbol', '').strip()
        quantity = request.data.get('quantity', 0)
        limit    = request.data.get('limit_price')  # optional
        idempotency_key = request.data.get("idempotency_key")

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"error": "quantity must be a whole number"}, status=400)

        try:
            if limit:
                limit_price = Decimal(str(limit))
                order = place_limit_sell(request.user, symbol, quantity, limit_price, idempotency_key=idempotency_key)
                msg = f"Limit sell placed for {quantity} shares of {symbol} at ₹{limit_price}"
            else:
                order = execute_sell(request.user, symbol, quantity, idempotency_key=idempotency_key)
                msg = f"Sold {quantity} shares of {symbol} at market price"

            return Response({
                "status": "success",
                "order_id": str(order.id),
                "order_status": order.status,
                "message": msg
            }, status=201)

        except InvalidOrderError          as e: return Response({"error": str(e)}, status=400)
        except InsufficientHoldingsError  as e: return Response({"error": str(e)}, status=400)
        except StockNotFoundError         as e: return Response({"error": str(e)}, status=404)
        except InvalidOperation           as e: return Response({"error": "Invalid limit price"}, status=400)
        except Exception                  as e: return Response({"error": str(e)}, status=500)

# Cancels a pending order.
class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            # call the cancel_order service function to attempt cancellation of the specified order
            order = cancel_order(request.user, order_id)
            
            # return success response 
            return Response({
                "status": "cancelled",
                "order_id": str(order.id),
                "message": "Order cancelled and funds refunded"
            })
    
        # track exceptions 
        except OrderCancellationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# Returns last 50 executed trades of the authenticated user, sorted by most recent first.
class TradeHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = TradeLog.objects.filter(
            student=request.user
        ).order_by('-executed_at')[:50]

        return Response([{
            "order_id":      str(l.order.id), 
            "symbol":        l.stock_symbol,
            "type":          l.order_type,
            "quantity":      l.quantity,
            "price":         float(l.price),
            "total_value":   float(l.total_value),
            "balance_after": float(l.wallet_balance_after),
            "time":          l.executed_at.isoformat()
        } for l in logs])

# Returns all pending orders of the authenticated user, sorted by most recent first.
class PendingOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            student=request.user,
            status=Order.Status.PENDING
        ).select_related('stock').order_by('-created_at')

        return Response([{
            "order_id":    str(o.id),
            "symbol":      o.stock.symbol,
            "type":        o.order_type,
            "quantity":    o.quantity,
            "limit_price": float(o.price_at_order),
            "total_value": float(o.total_value),
            "placed_at":   o.created_at.isoformat()
        } for o in orders])

# Returns a list of all stocks with their current price and last updated time.
class StockListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stocks = Stock.objects.all().order_by('sector', 'symbol')
        return Response([{
            "symbol":        s.symbol,
            "company":       s.company_name,
            "sector":        s.sector,
            "current_price": float(s.current_price),
            "last_updated":  s.last_updated.isoformat()
        } for s in stocks])