from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.contrib.auth import get_user_model

from .models import Lesson, Quiz, Question, QuizAttempt, Badge, UserBadge
from .serializers import (
    LessonSerializer, QuizSerializer, QuestionSerializer,
    QuizAttemptSerializer, QuizSubmitSerializer, BadgeSerializer, UserBadgeSerializer
)
from .services import check_and_award_badges

User = get_user_model()

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    @action(detail=True, methods=['post'])
    def add_quiz(self, request, pk=None):
        lesson = self.get_object()
        serializer = QuizSerializer(data=request.data)
        if serializer.is_valid():
            quiz = serializer.save(lesson=lesson)
            questions_data = request.data.get('questions', [])
            for q_data in questions_data:
                Question.objects.create(
                    quiz=quiz,
                    text=q_data['text'],
                    option_a=q_data['option_a'],
                    option_b=q_data['option_b'],
                    option_c=q_data['option_c'],
                    option_d=q_data['option_d'],
                    correct_option=q_data['correct_option']
                )
            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        
        # In a real app, user should be authenticated. For testing without auth,
        # we might need to rely on a passed user ID or just use first user.
        if not user.is_authenticated:
            user = User.objects.first()
            if not user:
                return Response({"error": "No user found in DB to attach attempt to."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = QuizSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        answers = serializer.validated_data['answers']
        questions = quiz.questions.all()
        
        if not questions.exists():
            return Response({"error": "No questions in this quiz."}, status=status.HTTP_400_BAD_REQUEST)

        correct_count = 0
        total_questions = questions.count()

        for question in questions:
            user_answer = answers.get(str(question.id))
            if user_answer and user_answer.upper() == question.correct_option:
                correct_count += 1
                
        score = (correct_count / total_questions) * 100

        attempt = QuizAttempt.objects.create(
            user=user,
            quiz=quiz,
            score=score
        )

        # Gamification
        new_badges = check_and_award_badges(user)
        badge_serializer = BadgeSerializer(new_badges, many=True)

        return Response({
            "score": score,
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "new_badges_awarded": badge_serializer.data
        }, status=status.HTTP_201_CREATED)


class LeaderboardViewSet(viewsets.ViewSet):
    def list(self, request):
        users = User.objects.annotate(
            total_score=Sum('quiz_attempts__score'),
            quizzes_taken=Count('quiz_attempts')
        ).order_by('-total_score')[:10]

        data = []
        for u in users:
            data.append({
                "user_id": u.id,
                "username": u.username,
                "total_score": u.total_score or 0,
                "quizzes_taken": u.quizzes_taken
            })
        
        return Response(data)

class UserProgressViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        
        attempts = QuizAttempt.objects.filter(user=user)
        badges = UserBadge.objects.filter(user=user)
        
        return Response({
            "username": user.username,
            "attempts": QuizAttemptSerializer(attempts, many=True).data,
            "badges": UserBadgeSerializer(badges, many=True).data
        })
