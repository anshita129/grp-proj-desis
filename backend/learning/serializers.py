from rest_framework import serializers
from .models import (
    Module, Lesson, LessonProgress, Quiz, Question, Choice,
    QuizAttempt, AttemptAnswer, Badge, UserBadge,
)


# ── Lessons ──────────────────────────────────────────────────

class LessonSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'order', 'completed']

    def get_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LessonProgress.objects.filter(user=request.user, lesson=obj).exists()
        return False


class LessonListSerializer(serializers.ModelSerializer):
    """Lighter serializer for lesson lists (no content body)."""
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'completed']

    def get_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LessonProgress.objects.filter(user=request.user, lesson=obj).exists()
        return False


# ── Modules ──────────────────────────────────────────────────

class ModuleListSerializer(serializers.ModelSerializer):
    total_lessons = serializers.IntegerField(read_only=True)
    lessons_done = serializers.IntegerField(read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'slug', 'description', 'difficulty', 'order',
                  'total_lessons', 'lessons_done']


class ModuleDetailSerializer(serializers.ModelSerializer):
    lessons = LessonListSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'slug', 'description', 'difficulty', 'order', 'lessons']


# ── Quizzes ──────────────────────────────────────────────────

class ChoiceSerializer(serializers.ModelSerializer):
    """Excludes is_correct — safe to send to the frontend before submission."""

    class Meta:
        model = Choice
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'choices']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'pass_mark', 'questions']


# ── Attempt submission ───────────────────────────────────────

class AnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField()


class SubmitAttemptSerializer(serializers.Serializer):
    answers = AnswerInputSerializer(many=True)

    def validate_answers(self, value):
        if len(value) != 10:
            raise serializers.ValidationError("Exactly 10 answers are required.")
        return value


# ── Attempt results ──────────────────────────────────────────

class ChoiceRevealSerializer(serializers.ModelSerializer):
    """Includes is_correct — only used AFTER submission on the results page."""

    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']


class AttemptAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_text = serializers.CharField(source='selected_choice.text', read_only=True)
    correct_choice = serializers.SerializerMethodField()

    class Meta:
        model = AttemptAnswer
        fields = ['question_text', 'selected_text', 'is_correct', 'correct_choice']

    def get_correct_choice(self, obj):
        correct = obj.question.choices.filter(is_correct=True).first()
        return correct.text if correct else None


class AttemptDetailSerializer(serializers.ModelSerializer):
    answers = AttemptAnswerSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    module_slug = serializers.CharField(source='quiz.module.slug', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz_title', 'module_slug', 'score', 'total_questions',
                  'passed', 'attempted_at', 'answers']


class AttemptListSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'score', 'total_questions', 'passed', 'attempted_at']


# ── Badges ───────────────────────────────────────────────────

class BadgeSerializer(serializers.ModelSerializer):
    awarded = serializers.SerializerMethodField()
    awarded_at = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon_name', 'awarded', 'awarded_at']

    def get_awarded(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserBadge.objects.filter(user=request.user, badge=obj).exists()
        return False

    def get_awarded_at(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            ub = UserBadge.objects.filter(user=request.user, badge=obj).first()
            return ub.awarded_at if ub else None
        return None


class NewBadgeSerializer(serializers.ModelSerializer):
    """Used in the quiz-submit response to show freshly earned badges."""

    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon_name']
