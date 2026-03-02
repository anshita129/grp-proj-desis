from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, QuizViewSet, LeaderboardViewSet, UserProgressViewSet

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')
router.register(r'users/progress', UserProgressViewSet, basename='user-progress')

urlpatterns = [
    path('', include(router.urls)),
]
