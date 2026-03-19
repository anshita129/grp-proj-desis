from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .market_data_view import MarketDataView, ScenariosView

router = DefaultRouter()
router.register(r'sessions', views.SimulationSessionViewSet, basename='simulation-session')

urlpatterns = [
    path('', include(router.urls)),
    path('run/', views.RunSimulationView.as_view(), name='run_simulation'),
    path('interactive/', views.InteractiveSimulationView.as_view(), name='interactive_simulation'),
    path('market-data/', MarketDataView.as_view(), name='market_data'),
    path('scenarios/', ScenariosView.as_view(), name='scenarios'),
]
