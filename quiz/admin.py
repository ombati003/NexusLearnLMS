from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import (
    Quiz,
    Progress,
    Question,
    MCQuestion,
    Choice,
    EssayQuestion,
    Sitting,
)


class ChoiceInline(admin.TabularInline):
    model = Choice


class QuizAdminForm(forms.ModelForm):
    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label="Questions",
        widget=FilteredSelectMultiple(verbose_name="Questions", is_stacked=False),
    )

    class Meta:
        model = Quiz
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["questions"].initial = (
                self.instance.question_set.all().select_subclasses()
            )

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm
    fields = ("title", "description")
    list_display = ("title",)
    search_fields = ("description", "category")


class MCQuestionAdmin(admin.ModelAdmin):
    list_display = ("content",)
    fieldsets = [
        ("Quiz Details", {"fields": ("content", "explanation")}),
    ]
    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)
    inlines = [ChoiceInline]


class ProgressAdmin(admin.ModelAdmin):
    search_fields = ("user", "score")


class EssayQuestionAdmin(admin.ModelAdmin):
    list_display = ("content",)
    fields = ("content", "quiz", "explanation")
    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)


admin.site.register(Quiz, QuizAdmin)
admin.site.register(MCQuestion, MCQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(EssayQuestion, EssayQuestionAdmin)
admin.site.register(Sitting)