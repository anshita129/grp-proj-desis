from rest_framework import serializers
from .models import Lesson, Quiz, Question, QuizAttempt, Badge, UserBadge
from django.contrib.auth import get_user_model

User = get_user_model()

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'option_a', 'option_b', 'option_c', 'option_d']
        # Do not expose correct_option to the client in the list

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'questions', 'created_at']

class LessonSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'order', 'quiz', 'created_at', 'updated_at']

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'user', 'quiz', 'score', 'completed_at']
        read_only_fields = ['user', 'score', 'completed_at']

class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
         child=serializers.CharField(max_length=1),
         help_text="Dictionary of question_id: option, e.g., {'1': 'A', '2': 'C'}"
    )

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon_url']

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'earned_at']
