""" from django.urls import path
from . import views

urlpatterns = [
    path("<slug>/quizzes/", views.quiz_list, name="quiz_index"),
    path("progress/", view=views.QuizUserProgressView.as_view(), name="quiz_progress"),
    # path('marking/<int:pk>/', view=QuizMarkingList.as_view(), name='quiz_marking'),
    path("marking_list/", view=views.QuizMarkingList.as_view(), name="quiz_marking"),
    path(
        "marking/<int:pk>/",
        view=views.QuizMarkingDetail.as_view(),
        name="quiz_marking_detail",
    ),
    path("<int:pk>/<slug>/take/", view=views.QuizTake.as_view(), name="quiz_take"),
    path("<slug>/quiz_add/", views.QuizCreateView.as_view(), name="quiz_create"),
    path("<slug>/<int:pk>/add/", views.QuizUpdateView.as_view(), name="quiz_update"),
    path("<slug>/<int:pk>/delete/", views.quiz_delete, name="quiz_delete"),
    path(
        "mc-question/add/<slug>/<int:quiz_id>/",
        views.MCQuestionCreate.as_view(),
        name="mc_create",
    ),
    # path('mc-question/add/<int:pk>/<quiz_pk>/', MCQuestionCreate.as_view(), name='mc_create'),
]
"""

from django.urls import path
from . import views

app_name = "quiz"

urlpatterns = [

    # =========================
    # Quiz list per course
    # =========================
    path(
        "<slug:slug>/quizzes/",
        views.quiz_list,
        name="quiz_index",
    ),

    # =========================
    # Quiz create / update / delete
    # =========================
    path(
        "<slug:slug>/quiz/add/",
        views.quiz_create,
        name="quiz_create",
    ),

    path(
        "<slug:slug>/quiz/<int:pk>/edit/",
        views.quiz_update,
        name="quiz_update",
    ),

    path(
        "<slug:slug>/quiz/<int:pk>/delete/",
        views.quiz_delete,
        name="quiz_delete",
    ),

    # =========================
    # Quiz taking
    # =========================
    path(
        "take/<int:pk>/<slug:slug>/",
        views.quiz_take,
        name="quiz_take",
    ),

    # =========================
    # MC Question creation
    # =========================
    path(
        "mc-question/add/<slug:slug>/<int:quiz_id>/",
        views.mcquestion_create,
        name="mc_create",
    ),

    # =========================
    # Progress & marking
    # =========================
    path(
        "progress/",
        views.QuizUserProgressView.as_view(),
        name="quiz_progress",
    ),

    path(
        "marking/",
        views.QuizMarkingList.as_view(),
        name="quiz_marking",
    ),

    path(
        "marking/<int:pk>/",
        views.QuizMarkingDetail.as_view(),
        name="quiz_marking_detail",
    ),
]

