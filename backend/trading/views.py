from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response

from trading.services.trade_service import execute_buy


@api_view(["POST"])
def buy_stock(request):
    user = request.user
    stock_id = request.data["stock_id"]
    quantity = int(request.data["quantity"])

    message = execute_buy(user, stock_id, quantity)

    return Response({"message": message})