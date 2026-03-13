from django.contrib import admin
from .models import (
    Module, Lesson, LessonProgress, Quiz, Question, Choice,
    QuizAttempt, AttemptAnswer, Badge, UserBadge,
)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'order')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module',)
    search_fields = ('title',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed_at')
    list_filter = ('lesson__module',)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'pass_mark')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [ChoiceInline]

    @admin.display(description='Question')
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__quiz')


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'is_correct')
    can_delete = False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total_questions', 'passed', 'attempted_at')
    list_filter = ('passed', 'quiz')
    inlines = [AttemptAnswerInline]
    readonly_fields = ('user', 'quiz', 'score', 'total_questions', 'passed')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_name')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge',)
