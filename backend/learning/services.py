from .models import Badge, UserBadge, QuizAttempt
from django.contrib.auth import get_user_model

User = get_user_model()

def check_and_award_badges(user):
    new_badges = []

    # Helper to award badge
    def award_badge(criteria_code):
        try:
            badge = Badge.objects.get(criteria_code=criteria_code)
            user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
            if created:
                new_badges.append(badge)
        except Badge.DoesNotExist:
            pass

    # Condition 1: First quiz completed
    attempts_count = QuizAttempt.objects.filter(user=user).count()
    if attempts_count == 1:
        award_badge('first_quiz')

    # Condition 2: Perfect Score
    perfect_scores = QuizAttempt.objects.filter(user=user, score=100.0).count()
    if perfect_scores > 0:
        award_badge('perfect_score')

    # Condition 3: Dedicated Learner (5+ quizzes)
    if attempts_count >= 5:
        award_badge('dedicated_learner')

    return new_badges
