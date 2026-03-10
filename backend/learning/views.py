from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Module, Lesson, LessonProgress, Quiz, Question, Choice,
    QuizAttempt, AttemptAnswer, Badge, UserBadge,
)
from .serializers import (
    ModuleListSerializer, ModuleDetailSerializer,
    LessonSerializer, QuizSerializer,
    SubmitAttemptSerializer, AttemptDetailSerializer, AttemptListSerializer,
    BadgeSerializer, NewBadgeSerializer,
)
from .badge_rules import evaluate_badges


# ── Modules ──────────────────────────────────────────────────

class ModuleListView(generics.ListAPIView):
    """GET /api/learning/modules/ — all modules with user progress counts."""
    serializer_class = ModuleListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Module.objects.annotate(
            total_lessons=Count('lessons'),
            lessons_done=Count(
                'lessons',
                filter=Q(lessons__progress__user=user),
            ),
        )


class ModuleDetailView(generics.RetrieveAPIView):
    """GET /api/learning/modules/<slug>/ — module with ordered lessons."""
    serializer_class = ModuleDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    queryset = Module.objects.all()


# ── Lessons ──────────────────────────────────────────────────

class LessonDetailView(generics.RetrieveAPIView):
    """GET /api/learning/lessons/<id>/ — single lesson."""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    queryset = Lesson.objects.all()


class CompleteLessonView(APIView):
    """POST /api/learning/lessons/<id>/complete/ — mark lesson complete."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={},
        )
        return Response({"detail": "Lesson marked as complete."}, status=status.HTTP_200_OK)


class ModuleProgressView(APIView):
    """GET /api/learning/modules/<slug>/progress/ — progress summary."""
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        module = get_object_or_404(Module, slug=slug)
        total = module.lessons.count()
        done = LessonProgress.objects.filter(
            user=request.user,
            lesson__module=module,
        ).count()
        quiz_unlocked = (done == total and total > 0)
        return Response({
            "lessons_done": done,
            "total": total,
            "quiz_unlocked": quiz_unlocked,
        })


# ── Quiz ─────────────────────────────────────────────────────

class QuizDetailView(APIView):
    """GET /api/learning/modules/<slug>/quiz/ — returns quiz if lessons complete."""
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        module = get_object_or_404(Module, slug=slug)

        # Check all lessons completed
        total = module.lessons.count()
        done = LessonProgress.objects.filter(
            user=request.user,
            lesson__module=module,
        ).count()
        if done < total:
            return Response(
                {"detail": f"Complete all lessons first ({done}/{total} done)."},
                status=status.HTTP_403_FORBIDDEN,
            )

        quiz = get_object_or_404(Quiz, module=module)
        serializer = QuizSerializer(quiz, context={'request': request})
        return Response(serializer.data)


class SubmitAttemptView(APIView):
    """POST /api/learning/quizzes/<id>/attempt/ — score and store attempt."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)

        serializer = SubmitAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data['answers']

        # Validate & score
        score = 0
        answer_objects = []
        for ans in answers:
            question = get_object_or_404(Question, pk=ans['question_id'], quiz=quiz)
            choice = get_object_or_404(Choice, pk=ans['choice_id'], question=question)
            correct = choice.is_correct
            if correct:
                score += 1
            answer_objects.append((question, choice, correct))

        total = quiz.questions.count()
        passed = score >= quiz.pass_mark

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            total_questions=total,
            passed=passed,
        )

        for question, choice, correct in answer_objects:
            AttemptAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_choice=choice,
                is_correct=correct,
            )

        # Badge evaluation
        newly_awarded = evaluate_badges(request.user, attempt)

        return Response({
            "attempt_id": attempt.id,
            "score": score,
            "total": total,
            "pass_mark": quiz.pass_mark,
            "passed": passed,
            "newly_awarded_badges": NewBadgeSerializer(newly_awarded, many=True).data,
        }, status=status.HTTP_201_CREATED)


class AttemptDetailView(generics.RetrieveAPIView):
    """GET /api/learning/attempts/<id>/ — full result with breakdown."""
    serializer_class = AttemptDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)


class MyAttemptsView(generics.ListAPIView):
    """GET /api/learning/quizzes/<id>/my-attempts/ — attempt history."""
    serializer_class = AttemptListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['pk'])
        return QuizAttempt.objects.filter(user=self.request.user, quiz=quiz)


# ── Badges ───────────────────────────────────────────────────

class BadgeListView(generics.ListAPIView):
    """GET /api/learning/badges/ — all badges with awarded status."""
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Badge.objects.all()


class MyBadgesView(generics.ListAPIView):
    """GET /api/learning/badges/mine/ — only earned badges."""
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        earned_ids = UserBadge.objects.filter(
            user=self.request.user
        ).values_list('badge_id', flat=True)
        return Badge.objects.filter(id__in=earned_ids)
