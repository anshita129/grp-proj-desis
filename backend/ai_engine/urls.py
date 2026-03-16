from django.urls import path
from .views import ai_feedback, ai_history, ai_chat, csrf_token_view

urlpatterns = [
    path("csrf/", csrf_token_view, name="csrf"),
    path("feedback/", ai_feedback, name="ai_feedback"),
    path("history/", ai_history, name="ai_history"),
    path("chat/", ai_chat, name="ai_chat"),
]