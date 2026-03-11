from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from learning.models import (
    Module, Lesson, LessonProgress, Quiz, Question, Choice,
    QuizAttempt, AttemptAnswer, Badge, UserBadge,
)
from learning.badge_rules import evaluate_badges

User = get_user_model()


class BadgeRulesTestCase(TestCase):
    """Unit tests for each badge rule in isolation."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass1234')

        # Create one module with one quiz
        self.module = Module.objects.create(title='Test Module', slug='test-module', order=1)
        self.quiz = Quiz.objects.create(module=self.module, title='Test Quiz', pass_mark=7)

        # Create 10 questions with correct choice
        for i in range(10):
            q = Question.objects.create(quiz=self.quiz, text=f'Q{i+1}', order=i+1)
            Choice.objects.create(question=q, text='Correct', is_correct=True)
            Choice.objects.create(question=q, text='Wrong', is_correct=False)

        # Create badges
        Badge.objects.create(name='First Quiz Passed', description='First pass', icon_name='star')
        Badge.objects.create(name='Perfect Score', description='10/10', icon_name='trophy')
        Badge.objects.create(name='All Modules Complete', description='All done', icon_name='crown')

    def _create_attempt(self, score, passed):
        return QuizAttempt.objects.create(
            user=self.user, quiz=self.quiz,
            score=score, total_questions=10, passed=passed,
        )

    def test_first_quiz_passed_badge(self):
        """First Quiz Passed badge is awarded on the first passing attempt."""
        attempt = self._create_attempt(score=8, passed=True)
        awarded = evaluate_badges(self.user, attempt)
        badge_names = [b.name for b in awarded]
        self.assertIn('First Quiz Passed', badge_names)

    def test_first_quiz_passed_not_duplicated(self):
        """First Quiz Passed badge is NOT awarded twice."""
        attempt1 = self._create_attempt(score=8, passed=True)
        evaluate_badges(self.user, attempt1)
        attempt2 = self._create_attempt(score=9, passed=True)
        awarded = evaluate_badges(self.user, attempt2)
        badge_names = [b.name for b in awarded]
        self.assertNotIn('First Quiz Passed', badge_names)

    def test_first_quiz_passed_not_on_fail(self):
        """First Quiz Passed badge is NOT awarded when quiz is failed."""
        attempt = self._create_attempt(score=4, passed=False)
        awarded = evaluate_badges(self.user, attempt)
        badge_names = [b.name for b in awarded]
        self.assertNotIn('First Quiz Passed', badge_names)

    def test_perfect_score_badge(self):
        """Perfect Score badge is awarded on 10/10."""
        attempt = self._create_attempt(score=10, passed=True)
        awarded = evaluate_badges(self.user, attempt)
        badge_names = [b.name for b in awarded]
        self.assertIn('Perfect Score', badge_names)

    def test_perfect_score_not_on_9(self):
        """Perfect Score badge is NOT awarded on 9/10."""
        attempt = self._create_attempt(score=9, passed=True)
        awarded = evaluate_badges(self.user, attempt)
        badge_names = [b.name for b in awarded]
        self.assertNotIn('Perfect Score', badge_names)

    def test_all_modules_complete_single_module(self):
        """All Modules Complete badge IS awarded when all modules (just 1 here) are passed."""
        attempt = self._create_attempt(score=8, passed=True)
        awarded = evaluate_badges(self.user, attempt)
        badge_names = [b.name for b in awarded]
        self.assertIn('All Modules Complete', badge_names)

    def test_all_modules_complete_not_when_missing(self):
        """All Modules Complete badge is NOT awarded when some modules have no passing attempt."""
        # Add a second module with no attempt
        Module.objects.create(title='Module 2', slug='module-2', order=2)
        attempt = self._create_attempt(score=8, passed=True)
        awarded = evaluate_badges(self.user, attempt)
        badge_names = [b.name for b in awarded]
        self.assertNotIn('All Modules Complete', badge_names)


class QuizSubmitIntegrationTest(TestCase):
    """End-to-end test: seed data → complete lessons → submit quiz → check response."""

    def setUp(self):
        self.user = User.objects.create_user(username='quizuser', password='pass1234')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create module, lessons, quiz
        self.module = Module.objects.create(title='Integration Module', slug='integration-module', order=1)
        for i in range(3):
            Lesson.objects.create(module=self.module, title=f'Lesson {i+1}', content='Content', order=i+1)
        self.quiz = Quiz.objects.create(module=self.module, title='Integration Quiz', pass_mark=7)

        self.questions = []
        self.correct_choices = []
        self.wrong_choices = []
        for i in range(10):
            q = Question.objects.create(quiz=self.quiz, text=f'Question {i+1}', order=i+1)
            correct = Choice.objects.create(question=q, text='Correct', is_correct=True)
            wrong = Choice.objects.create(question=q, text='Wrong', is_correct=False)
            self.questions.append(q)
            self.correct_choices.append(correct)
            self.wrong_choices.append(wrong)

        Badge.objects.create(name='First Quiz Passed', description='First', icon_name='star')
        Badge.objects.create(name='Perfect Score', description='Perfect', icon_name='trophy')
        Badge.objects.create(name='All Modules Complete', description='All', icon_name='crown')

    def test_quiz_403_when_lessons_incomplete(self):
        """GET quiz returns 403 when not all lessons are complete."""
        resp = self.client.get(f'/api/learning/modules/{self.module.slug}/quiz/')
        self.assertEqual(resp.status_code, 403)

    def test_full_quiz_pass_flow(self):
        """Complete lessons → submit quiz with all correct → score 10, passed, badges awarded."""
        # Complete all lessons
        for lesson in self.module.lessons.all():
            self.client.post(f'/api/learning/lessons/{lesson.id}/complete/')

        # Verify quiz is now accessible
        resp = self.client.get(f'/api/learning/modules/{self.module.slug}/quiz/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['questions']), 10)

        # Submit all correct answers
        answers = [
            {'question_id': q.id, 'choice_id': c.id}
            for q, c in zip(self.questions, self.correct_choices)
        ]
        resp = self.client.post(
            f'/api/learning/quizzes/{self.quiz.id}/attempt/',
            {'answers': answers},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['score'], 10)
        self.assertTrue(resp.data['passed'])
        # Should get First Quiz Passed, Perfect Score, and All Modules Complete
        badge_names = [b['name'] for b in resp.data['newly_awarded_badges']]
        self.assertIn('First Quiz Passed', badge_names)
        self.assertIn('Perfect Score', badge_names)
        self.assertIn('All Modules Complete', badge_names)

    def test_quiz_fail_flow(self):
        """Submit quiz with all wrong answers → score 0, failed."""
        # Complete lessons first
        for lesson in self.module.lessons.all():
            self.client.post(f'/api/learning/lessons/{lesson.id}/complete/')

        # Submit all wrong answers
        answers = [
            {'question_id': q.id, 'choice_id': c.id}
            for q, c in zip(self.questions, self.wrong_choices)
        ]
        resp = self.client.post(
            f'/api/learning/quizzes/{self.quiz.id}/attempt/',
            {'answers': answers},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['score'], 0)
        self.assertFalse(resp.data['passed'])
        self.assertEqual(len(resp.data['newly_awarded_badges']), 0)

    def test_attempt_detail_reveals_correct_answers(self):
        """GET /attempts/:id/ reveals correct answers in the breakdown."""
        for lesson in self.module.lessons.all():
            self.client.post(f'/api/learning/lessons/{lesson.id}/complete/')

        answers = [
            {'question_id': q.id, 'choice_id': c.id}
            for q, c in zip(self.questions, self.wrong_choices)
        ]
        resp = self.client.post(
            f'/api/learning/quizzes/{self.quiz.id}/attempt/',
            {'answers': answers}, format='json',
        )
        attempt_id = resp.data['attempt_id']

        detail = self.client.get(f'/api/learning/attempts/{attempt_id}/')
        self.assertEqual(detail.status_code, 200)
        # Each answer should have correct_choice revealed
        for a in detail.data['answers']:
            self.assertIn('correct_choice', a)
            self.assertEqual(a['correct_choice'], 'Correct')

    def test_module_progress_endpoint(self):
        """GET /modules/:slug/progress/ returns correct counts."""
        resp = self.client.get(f'/api/learning/modules/{self.module.slug}/progress/')
        self.assertEqual(resp.data['lessons_done'], 0)
        self.assertEqual(resp.data['total'], 3)
        self.assertFalse(resp.data['quiz_unlocked'])

        # Complete one lesson
        lesson = self.module.lessons.first()
        self.client.post(f'/api/learning/lessons/{lesson.id}/complete/')

        resp = self.client.get(f'/api/learning/modules/{self.module.slug}/progress/')
        self.assertEqual(resp.data['lessons_done'], 1)
        self.assertFalse(resp.data['quiz_unlocked'])

    def test_badges_endpoint(self):
        """GET /badges/ returns all badges with awarded=False initially."""
        resp = self.client.get('/api/learning/badges/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)
        for b in resp.data:
            self.assertFalse(b['awarded'])
