from rest_framework.views import APIView # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.permissions import IsAuthenticated # type: ignore
from .models import Wallet, Holding, TradeLog, Stock, Order, LimitOrder
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from django.core.cache import cache
from django.utils.dateparse import parse_datetime

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
        expires  = request.data.get('expires_at')
        expires_at = parse_datetime(expires) if expires else None
        if expires_at and expires_at <= datetime.now(timezone.utc):
            return Response({"error": "Expiry time must be in the future"}, status=400)
  
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"error": "quantity must be a whole number"}, status=400)

        try:
            # depending on whether limit price is provided, call the appropriate service function to execute the buy order
            if limit:
                limit_price = Decimal(str(limit))
                order = place_limit_buy(request.user, symbol, quantity, limit_price, expires_at=expires, idempotency_key=idempotency_key)
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
        limit    = request.data.get('limit_price')  
        idempotency_key = request.data.get("idempotency_key")

        expires  = request.data.get('expires_at')
        expires_at = parse_datetime(expires) if expires else None
        if expires_at and expires_at <= datetime.now(timezone.utc):
            return Response({"error": "Expiry time must be in the future"}, status=400)
        
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"error": "quantity must be a whole number"}, status=400)

        try:
            if limit:
                limit_price = Decimal(str(limit))
                order = place_limit_sell(request.user, symbol, quantity, limit_price, expires_at=expires, idempotency_key=idempotency_key)
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

# Cancels a pending order
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
        

class TradeHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all orders, apart from pending orders 
        orders = Order.objects.filter(
                student=request.user,
                status__in=[Order.Status.EXECUTED, Order.Status.CANCELLED]  # exclude PENDING
            ).order_by('-created_at')[:50]
                
        # Get trade logs keyed by order id for balance info
        logs = {str(l.order.id): l for l in TradeLog.objects.filter(order__student=request.user)}
        
        limit_prices = {str(l.order.id): float(l.limit_price) 
                for l in LimitOrder.objects.filter(order__student=request.user)}

        result = []
        for o in orders:
            log = logs.get(str(o.id))
            result.append({
                "order_id":      str(o.id),
                "symbol":        o.stock.symbol,
                "type":          o.order_type,
                "quantity":      o.quantity,
                "price":         round(float(log.price if log else o.price_at_order), 2),
                "total_value":   round(float(log.total_value if log else o.price_at_order * o.quantity), 2),
                "limit_price":   round(float(limit_prices[str(o.id)]), 2) if str(o.id) in limit_prices else None,
                "balance_after": float(log.wallet_balance_after) if log else None,
                "time":          o.created_at.isoformat(),
                "executed_at":   log.executed_at.isoformat() if log else None,
                "status":        o.status,
                "is_limit":      str(o.id) in limit_prices,
                
            })
        return Response(result)

# Returns all pending orders of the authenticated user, sorted by most recent first.
class PendingOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            student=request.user,
            status=Order.Status.PENDING
        ).select_related('stock').order_by('-created_at')

        # pre-fetch limit prices for all these orders
        limit_map = {
            str(lo.order.id): {"limit_price": round(float(lo.limit_price), 2), "expires_at": lo.expires_at.isoformat() if lo.expires_at else None}
            for lo in LimitOrder.objects.filter(order__in=orders)
        }

        return Response([{
            "id":             str(o.id),
            "stock":          o.stock.symbol,
            "order_type":     o.order_type,
            "quantity":       o.quantity,
            "price_at_order": round(float(o.price_at_order), 2),
            "limit_price":    limit_map.get(str(o.id), {}).get("limit_price"),
            "expires_at":     limit_map.get(str(o.id), {}).get("expires_at"),
            "created_at":     o.created_at.isoformat(),
        } for o in orders])
    

# Returns a list of all stocks with their current price and last updated time
class StockListView(APIView):
    permission_classes = []

    def get(self, request):
        stocks = Stock.objects.all().order_by('sector', 'symbol')
        return Response([{
            "symbol":        s.symbol,
            "company":       s.company_name,
            "sector":        s.sector,
            "current_price": float(s.current_price),
            "prev_close":    cache.get(f'prev_close_{s.symbol}', float(s.current_price)),
            "last_updated":  s.last_updated.isoformat()
        } for s in stocks])

# Returns the wallet balance of the authenticated user. If wallet doesn't exist, returns balance as 0.0
class WalletView(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request):
        from trading.models import Wallet
        try:
            wallet = Wallet.objects.get(student=request.user)
            return Response({"wallet_balance": float(wallet.balance)})
        except Wallet.DoesNotExist:
            return Response({"wallet_balance": 0.0})
        
# Returns a list of all holdings for the authenticated user
class HoldingsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        holdings = Holding.objects.filter(
            student=request.user, quantity__gt=0
        ).select_related('stock')
        return Response([{
            "symbol": h.stock.symbol,
            "quantity": h.quantity,
        } for h in holdings])
