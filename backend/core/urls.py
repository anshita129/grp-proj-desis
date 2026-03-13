"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/users/', include('users.urls')),
    path("portfolio/", include("portfolio.urls")),
    path("api-auth/", include("rest_framework.urls")),

    path('api/trading/', include('trading.urls')),
    path("api/ai/", include("ai_engine.urls")),

    path('api/simulation/', include('simulation.urls')),
    path('api/learning/', include('learning.urls')),
]