from django.urls import path
from .views import test_api, login_view, logout_view, me_view, profile_view
urlpatterns = [
    path('test/', test_api),
    path('login/', login_view),
    path('logout/', logout_view),
    path('me/', me_view),
    path("profile/", profile_view, name="profile"),
]