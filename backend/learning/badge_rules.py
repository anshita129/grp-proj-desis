"""
Badge rule engine.

evaluate_badges(user, attempt) → list of newly awarded Badge instances.
Called synchronously at the end of SubmitAttemptView.
"""
from .models import Badge, UserBadge, QuizAttempt, Module


def evaluate_badges(user, attempt):
    """Return a list of Badge objects that were freshly awarded."""
    newly_awarded = []

    # ── Rule 1: First Quiz Passed ─────────────────────────────
    if attempt.passed:
        badge = Badge.objects.filter(name="First Quiz Passed").first()
        if badge and not UserBadge.objects.filter(user=user, badge=badge).exists():
            # Check that this is indeed the first passed attempt ever
            first_pass_count = QuizAttempt.objects.filter(user=user, passed=True).count()
            if first_pass_count == 1:  # the current attempt is the only one
                UserBadge.objects.create(user=user, badge=badge)
                newly_awarded.append(badge)

    # ── Rule 2: Perfect Score ─────────────────────────────────
    if attempt.score == attempt.total_questions:
        badge = Badge.objects.filter(name="Perfect Score").first()
        if badge and not UserBadge.objects.filter(user=user, badge=badge).exists():
            UserBadge.objects.create(user=user, badge=badge)
            newly_awarded.append(badge)

    # ── Rule 3: All Modules Complete ──────────────────────────
    if attempt.passed:
        total_modules = Module.objects.count()
        # A module is "complete" when the user has at least one passed attempt on its quiz
        passed_modules = (
            QuizAttempt.objects
            .filter(user=user, passed=True)
            .values('quiz__module')
            .distinct()
            .count()
        )
        if passed_modules >= total_modules and total_modules > 0:
            badge = Badge.objects.filter(name="All Modules Complete").first()
            if badge and not UserBadge.objects.filter(user=user, badge=badge).exists():
                UserBadge.objects.create(user=user, badge=badge)
                newly_awarded.append(badge)

    return newly_awarded
