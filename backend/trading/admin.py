# Register your models here.
from django.contrib import admin
from .models import Order, Wallet, Stock, Holding, TradeLog

admin.site.register(Order)
admin.site.register(Wallet)
admin.site.register(Stock)
admin.site.register(Holding)
admin.site.register(TradeLog)
