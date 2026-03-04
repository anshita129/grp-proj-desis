from django.urls import path
from . import views

urlpatterns = [
    path('run/', views.RunSimulationView.as_view(), name='run_simulation'),
    path('interactive/', views.InteractiveSimulationView.as_view(), name='interactive_simulation'),
]
