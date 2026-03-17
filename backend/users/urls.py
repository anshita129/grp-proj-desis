from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api),
    path('csrf/', views.csrf, name='csrf'),
    path('me/', views.me, name='me'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('oauth/status/', views.oauth_status, name='oauth_status'),
    path('password/forgot/', views.forgot_password, name='forgot_password'),
    path('password/verify-otp/', views.verify_otp, name='verify_otp'),
    path('password/reset/', views.reset_password, name='reset_password'),
]
