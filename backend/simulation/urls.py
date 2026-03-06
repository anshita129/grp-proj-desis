from django.urls import path
from . import views
from .market_data_view import MarketDataView

urlpatterns = [
    path('run/', views.RunSimulationView.as_view(), name='run_simulation'),
    path('interactive/', views.InteractiveSimulationView.as_view(), name='interactive_simulation'),
    path('market-data/', MarketDataView.as_view(), name='market_data'),
]
