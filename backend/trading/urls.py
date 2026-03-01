from django.urls import path
from . import views
 
urlpatterns = [
    path('buy/',       views.BuyView.as_view(),         name='trade-buy'),
    path('sell/',      views.SellView.as_view(),        name='trade-sell'),
    path('portfolio/', views.PortfolioView.as_view(),   name='portfolio'),
    path('history/',   views.TradeHistoryView.as_view(), name='trade-history'),
]
