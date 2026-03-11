from django.urls import path
from . import views

urlpatterns = [
    # Modules
    path('modules/', views.ModuleListView.as_view(), name='module-list'),
    path('modules/<slug:slug>/', views.ModuleDetailView.as_view(), name='module-detail'),
    path('modules/<slug:slug>/progress/', views.ModuleProgressView.as_view(), name='module-progress'),
    path('modules/<slug:slug>/quiz/', views.QuizDetailView.as_view(), name='quiz-detail'),

    # Lessons
    path('lessons/<int:pk>/', views.LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/complete/', views.CompleteLessonView.as_view(), name='lesson-complete'),

    # Quizzes
    path('quizzes/<int:pk>/attempt/', views.SubmitAttemptView.as_view(), name='quiz-attempt'),
    path('quizzes/<int:pk>/my-attempts/', views.MyAttemptsView.as_view(), name='my-attempts'),

    # Attempts
    path('attempts/<int:pk>/', views.AttemptDetailView.as_view(), name='attempt-detail'),

    # Badges
    path('badges/', views.BadgeListView.as_view(), name='badge-list'),
    path('badges/mine/', views.MyBadgesView.as_view(), name='my-badges'),
]
