from decimal import Decimal
from .models import Badge, UserBadge, QuizAttempt, Module
from trading.models import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

def check_and_award_badges(user):
    new_badges = []

    def award_badge(name):
        try:
            badge = Badge.objects.get(name=name)
            user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
            if created:
                new_badges.append(badge)
                # Add reward cash to the user's trading wallet
                if badge.reward_amount > 0:
                    wallet, _ = Wallet.objects.get_or_create(student=user)
                    wallet.balance += Decimal(str(badge.reward_amount))
                    wallet.save()
        except Badge.DoesNotExist:
            pass

    attempts_count = QuizAttempt.objects.filter(user=user).count()
    if attempts_count >= 1:
        award_badge('First Quiz Passed')

    perfect_scores = QuizAttempt.objects.filter(user=user, score=100.0).count()
    if perfect_scores > 0:
        award_badge('Perfect Score')

    # Check for "All Modules Complete" badge
    total_modules = Module.objects.count()
    passed_modules = QuizAttempt.objects.filter(user=user, passed=True).values('quiz__module').distinct().count()
    if total_modules > 0 and passed_modules >= total_modules:
        award_badge('All Modules Complete')

    if attempts_count >= 5:
        award_badge('Dedicated Learner')

    return new_badges
