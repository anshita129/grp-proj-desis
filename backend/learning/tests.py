from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Lesson, Quiz, Question, QuizAttempt, Badge

User = get_user_model()

class LearningAPITests(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='test_student', password='password123')
        self.client.force_authenticate(user=self.user)
        
        # Create badges since gamification relies on them
        Badge.objects.create(name="First Quiz", description="Completed your first quiz", criteria_code="first_quiz")
        Badge.objects.create(name="Perfect Score", description="Got 100% on a quiz", criteria_code="perfect_score")
        Badge.objects.create(name="Dedicated Learner", description="Completed 5 quizzes", criteria_code="dedicated_learner")

    def test_create_lesson(self):
        url = reverse('lesson-list')
        data = {
            "title": "Introduction to Stock Market",
            "content": "This is a basic lesson about stocks.",
            "order": 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(Lesson.objects.get().title, "Introduction to Stock Market")

    def test_add_quiz_to_lesson(self):
        lesson = Lesson.objects.create(title="Test Lesson", content="Content", order=1)
        url = reverse('lesson-add-quiz', args=[lesson.id])
        data = {
            "title": "Quiz 1: Basics",
            "questions": [
                {
                    "text": "What is a stock?",
                    "option_a": "A type of soup",
                    "option_b": "A share of ownership in a company",
                    "option_c": "A livestock animal",
                    "option_d": "None of the above",
                    "correct_option": "B"
                },
                {
                    "text": "What does IPO stand for?",
                    "option_a": "Initial Public Offering",
                    "option_b": "Internal Profit Organization",
                    "option_c": "International Portfolio Option",
                    "option_d": "Internet Protocol Output",
                    "correct_option": "A"
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 2)

    def test_submit_quiz_and_gamification(self):
        # Setup Quiz
        lesson = Lesson.objects.create(title="Test Lesson", content="Content", order=1)
        quiz = Quiz.objects.create(lesson=lesson, title="Test Quiz")
        q1 = Question.objects.create(quiz=quiz, text="Q1", option_a="1", option_b="2", option_c="3", option_d="4", correct_option="A")
        q2 = Question.objects.create(quiz=quiz, text="Q2", option_a="1", option_b="2", option_c="3", option_d="4", correct_option="B")

        url = reverse('quiz-submit', args=[quiz.id])
        data = {
            "answers": {
                str(q1.id): "A",
                str(q2.id): "B"
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check score calculation
        self.assertEqual(response.data['score'], 100.0)
        self.assertEqual(QuizAttempt.objects.count(), 1)
        
        # Gamification hooks (should have gotten First Quiz and Perfect Score)
        earned_badges = response.data['new_badges_awarded']
        self.assertEqual(len(earned_badges), 2)
        badge_names = [b['name'] for b in earned_badges]
        self.assertIn("First Quiz", badge_names)
        self.assertIn("Perfect Score", badge_names)

    def test_leaderboard_and_progress(self):
        # Creating mock attempts to test leaderboard mapping
        lesson = Lesson.objects.create(title="L1", content="C1", order=1)
        quiz = Quiz.objects.create(lesson=lesson, title="Q1")
        QuizAttempt.objects.create(user=self.user, quiz=quiz, score=100.0)

        # Leaderboard
        leaderboard_url = reverse('leaderboard-list')
        res_leaderboard = self.client.get(leaderboard_url)
        self.assertEqual(res_leaderboard.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_leaderboard.data), 1)
        self.assertEqual(res_leaderboard.data[0]['total_score'], 100.0)

        # User Progress
        progress_url = reverse('user-progress-detail', args=[self.user.id])
        res_progress = self.client.get(progress_url)
        self.assertEqual(res_progress.status_code, status.HTTP_200_OK)
        self.assertEqual(res_progress.data['username'], self.user.username)
        self.assertEqual(len(res_progress.data['attempts']), 1)
