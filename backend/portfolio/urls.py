from django.urls import path
from .views import portfolio_view

urlpatterns = [
    path("my-portfolio/", portfolio_view),
]