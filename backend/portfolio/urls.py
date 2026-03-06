from django.urls import path
from .views.portfolio_view import PortfolioView

urlpatterns = [
    path("my-portfolio/", PortfolioView.as_view() , name = "MyPortfolio"),
]