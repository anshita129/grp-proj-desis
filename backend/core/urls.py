from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    
    path('accounts/', include('allauth.urls')),

    path('api/users/', include('users.urls')),
    path("api/portfolio/", include("portfolio.urls")),
    path("api-auth/", include("rest_framework.urls")),

    path('api/trading/', include('trading.urls')),
    path("api/ai/", include("ai_engine.urls")),

    path('api/simulation/', include('simulation.urls')),
    path('api/learning/', include('learning.urls')),
]