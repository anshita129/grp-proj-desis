from django.urls import path
from .views import ai_feedback, ai_history

urlpatterns = [
    path("feedback/", ai_feedback),
    path("history/", ai_history),
]