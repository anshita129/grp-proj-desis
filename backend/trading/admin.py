

# Register your models here.
from django.contrib import admin
from .models import Trade, Wallet, Stock

admin.site.register(Trade)
admin.site.register(Wallet)
admin.site.register(Stock)
