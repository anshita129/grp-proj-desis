# Register your models here.
from django.contrib import admin
from .models import LimitOrder, Order, Wallet, Stock, Holding, TradeLog, DailyStockPrice

admin.site.register(Order)
admin.site.register(Wallet)
admin.site.register(Stock)
admin.site.register(Holding)
admin.site.register(TradeLog)
admin.site.register(LimitOrder)
admin.site.register(DailyStockPrice)
