from django.urls import path
from . import views
 
urlpatterns = [
    path('buy/',       views.BuyView.as_view(),         name='trade-buy'),
    path('sell/',      views.SellView.as_view(),        name='trade-sell'),
    path('portfolio/', views.PortfolioView.as_view(),   name='portfolio'),
    path('history/',   views.TradeHistoryView.as_view(), name='trade-history'),
    path('orders/pending/', views.PendingOrdersView.as_view(), name='pending-orders'),
    path('orders/history/', views.OrderHistoryView.as_view(), name='order-history'),
    path('order/<uuid:order_id>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
]
