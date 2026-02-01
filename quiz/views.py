from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.decorators import lecturer_required
from .models import (
    Choice,
    Course,
    EssayQuestion,
    MCQuestion,
    Progress,
    Question,
    Quiz,
    Sitting,
)


# ########################################################
# Quiz Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
def quiz_create(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if request.method == "POST":
        category = request.POST.get("category")
        title = request.POST.get("title")
        pass_mark = request.POST.get("pass_mark")
        description = request.POST.get("description")
        random_order = request.POST.get("random_order") == "on"
        answers_at_end = request.POST.get("answers_at_end") == "on"
        exam_paper = request.POST.get("exam_paper") == "on"
        single_attempt = request.POST.get("single_attempt") == "on"
        draft = request.POST.get("draft") == "on"

        if not title:
            messages.error(request, "Title is required.")
        else:
            with transaction.atomic():
                quiz = Quiz.objects.create(
                    course=course,
                    category=category,
                    title=title,
                    pass_mark=pass_mark,
                    description=description,
                    random_order=random_order,
                    answers_at_end=answers_at_end,
                    exam_paper=exam_paper,
                    single_attempt=single_attempt,
                    draft=draft,
                )
            messages.success(request, f"Quiz '{quiz.title}' created successfully!")
            return redirect("mc_create", slug=course.slug, quiz_id=quiz.id)

    return render(
        request,
        "quiz/quiz_form.html",  # your cleaned template
        {
            "title": "Create Quiz",
            "course": course,
        },
    )



@method_decorator([login_required, lecturer_required], name="dispatch")
def quiz_update(request, slug, pk):
    course = get_object_or_404(Course, slug=slug)
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == "POST":
        title = request.POST.get("title")
        category = request.POST.get("category")
        pass_mark = request.POST.get("pass_mark")
        description = request.POST.get("description")
        random_order = request.POST.get("random_order") == "on"
        answers_at_end = request.POST.get("answers_at_end") == "on"
        exam_paper = request.POST.get("exam_paper") == "on"
        single_attempt = request.POST.get("single_attempt") == "on"
        draft = request.POST.get("draft") == "on"

        if not title:
            messages.error(request, "Title is required.")
        else:
            with transaction.atomic():
                quiz.title = title
                quiz.category = category
                quiz.pass_mark = pass_mark
                quiz.description = description
                quiz.random_order = random_order
                quiz.answers_at_end = answers_at_end
                quiz.exam_paper = exam_paper
                quiz.single_attempt = single_attempt
                quiz.draft = draft
                quiz.save()

            messages.success(request, f"Quiz '{quiz.title}' updated successfully!")
            return redirect("quiz_index", slug=course.slug)

    return render(
        request,
        "quiz/quiz_form.html",  # your cleaned template
        {
            "title": "Edit Quiz",
            "course": course,
            "quiz": quiz,
        },
    )



@login_required
@lecturer_required
def quiz_delete(request, slug, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.delete()
    messages.success(request, "Quiz successfully deleted.")
    return redirect("quiz_index", slug=slug)


@login_required
def quiz_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    quizzes = Quiz.objects.filter(course=course).order_by("-timestamp")
    return render(
        request, "quiz/quiz_list.html", {"quizzes": quizzes, "course": course}
    )


# ########################################################
# Multiple Choice Question Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
def mcquestion_create(request, slug, quiz_id):
    course = get_object_or_404(Course, slug=slug)
    quiz_obj = get_object_or_404(Quiz, id=quiz_id)
    quiz_questions_count = Question.objects.filter(quiz=quiz_obj).count()

    if request.method == "POST":
        content = request.POST.get("content")
        figure = request.POST.get("figure")
        explanation = request.POST.get("explanation")
        choice_order = request.POST.get("choice_order")

        if not content:
            messages.error(request, "Content is required.")
        else:
            with transaction.atomic():
                mc_question = MCQuestion.objects.create(
                    content=content,
                    figure=figure,
                    explanation=explanation,
                    choice_order=choice_order,
                )
                mc_question.quiz.add(quiz_obj)

                # Save choices manually
                for i in range(1, 5):
                    text = request.POST.get(f"choice_text_{i}")
                    correct = request.POST.get(f"correct_{i}") == "on"
                    if text:
                        Choice.objects.create(
                            question=mc_question,
                            choice_text=text,
                            correct=correct,
                        )

            if "another" in request.POST:
                messages.success(request, "Question added successfully. You can add another.")
                return redirect("mc_create", slug=slug, quiz_id=quiz_id)

            messages.success(request, "Question added successfully.")
            return redirect("quiz_index", slug=slug)

    return render(
        request,
        "quiz/mcquestion_form.html",
        {
            "course": course,
            "quiz_obj": quiz_obj,
            "quiz_questions_count": quiz_questions_count,
        },
    )



# ########################################################
# Quiz Progress and Marking Views
# ########################################################


@method_decorator([login_required], name="dispatch")
class QuizUserProgressView(TemplateView):
    template_name = "quiz/progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        context["exams_counter"] = context["exams"].count()
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingList(ListView):
    model = Sitting
    template_name = "quiz/quiz_marking_list.html"

    def get_queryset(self):
        queryset = Sitting.objects.filter(complete=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                quiz__course__allocated_course__lecturer__pk=self.request.user.id
            )
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)
        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        return queryset


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingDetail(DetailView):
    model = Sitting
    template_name = "quiz/quiz_marking_detail.html"

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()
        question_id = request.POST.get("qid")
        if question_id:
            question = Question.objects.get_subclass(id=int(question_id))
            if int(question_id) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(question)
            else:
                sitting.add_incorrect_question(question)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.get_questions(with_answers=True)
        return context


# ########################################################
# Quiz Taking View
# ########################################################


@login_required
@lecturer_required
def quiz_take(request, pk, slug):
    course = get_object_or_404(Course, pk=pk)
    quiz = get_object_or_404(Quiz, slug=slug, course=course)

    # Ensure quiz has questions
    if not Question.objects.filter(quiz=quiz).exists():
        messages.warning(request, "This quiz has no questions available.")
        return redirect("quiz_index", slug=course.slug)

    # Get sitting for this user
    sitting = Sitting.objects.user_sitting(request.user, quiz, course)
    if not sitting:
        messages.info(request, "You have already completed this quiz. Only one attempt is permitted.")
        return redirect("quiz_index", slug=course.slug)

    # Current question + progress
    question = sitting.get_first_question()
    progress = sitting.progress()
    previous = {}

    if request.method == "POST":
        # Manual answer handling
        guess = request.POST.get("answers")  # matches <input name="answers"> in template
        if guess:
            progress_obj, _ = Progress.objects.get_or_create(user=request.user)
            is_correct = question.check_if_correct(guess)

            if is_correct:
                sitting.add_to_score(1)
                progress_obj.update_score(question, 1, 1)
            else:
                sitting.add_incorrect_question(question)
                progress_obj.update_score(question, 0, 1)

            if not quiz.answers_at_end:
                previous = {
                    "previous_answer": guess,
                    "previous_outcome": is_correct,
                    "previous_question": question,
                    "answers": question.get_choices(),
                    "question_type": {question.__class__.__name__: True},
                }

            sitting.add_user_answer(question, guess)
            sitting.remove_first_question()

            # Update for next round
            question = sitting.get_first_question()
            progress = sitting.progress()

            # If no more questions → final result
            if not question:
                return final_result_user(request, sitting, quiz, course, previous)

    return render(
        request,
        "quiz/question.html",
        {
            "quiz": quiz,
            "course": course,
            "question": question,
            "progress": progress,
            "previous": previous,
        },
    )


def final_result_user(request, sitting, quiz, course, previous):
    sitting.mark_quiz_complete()
    results = {
        "course": course,
        "quiz": quiz,
        "score": sitting.get_current_score,
        "max_score": sitting.get_max_score,
        "percent": sitting.get_percent_correct,
        "sitting": sitting,
        "previous": previous,
    }

    if quiz.answers_at_end:
        results["questions"] = sitting.get_questions(with_answers=True)
        results["incorrect_questions"] = sitting.get_incorrect_questions

    # Delete sitting if not exam paper or user is privileged
    if (not quiz.exam_paper or request.user.is_superuser or request.user.is_lecturer):
        sitting.delete()

    return render(request, "quiz/result.html", results)

