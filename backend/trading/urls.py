from django.urls import path
from . import views
from portfolio.views.portfolio_view import PortfolioView

urlpatterns = [
    path('buy/',                        views.BuyView.as_view(),          name='trade-buy'),
    path('sell/',                       views.SellView.as_view(),         name='trade-sell'),
    path('portfolio/', PortfolioView.as_view(), name='portfolio'),
    path('cancel/<uuid:order_id>/',     views.CancelOrderView.as_view(),  name='trade-cancel'),
    path('history/',                    views.TradeHistoryView.as_view(), name='trade-history'),
    path('orders/pending/',             views.PendingOrdersView.as_view(),name='pending-orders'),
    path('stocks/',                     views.StockListView.as_view(),    name='stock-list'),
    path('orders/history/', views.OrderHistoryView.as_view(), name='order-history'),
]

