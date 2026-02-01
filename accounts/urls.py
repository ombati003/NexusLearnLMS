from django.urls import path, include

# from django.contrib.auth.views import (
#     PasswordResetView,
#     PasswordResetDoneView,
#     PasswordResetConfirmView,
#     PasswordResetCompleteView,
#     LoginView,
#     LogoutView,
# )
from . views import *
""" from .views import (
    home, lec, stud, sidebar, navbar,
    profile,
    profile_single,
    admin_panel,
    profile_update,
    change_password,
    LecturerFilterView,
    StudentListView,
    staff_add_view,
    edit_staff,
    delete_staff,
    student_add_view,
    edit_student,
    delete_student,
    edit_student_program,
    validate_username,
    register,
    render_lecturer_pdf_list,  # new
    render_student_pdf_list,  # new
)  """

# from .forms import EmailValidationOnForgotPassword

"""" path("/hm", home, name="home"),
    path("lec", lec, name="lec"),
    path("stud", stud, name="stud"),
    path("sidebar", sidebar, name="sidebar"),
    path("navbar", navbar, name="navbar"), """

urlpatterns = [

    path("", include("django.contrib.auth.urls")),
    path("admin_panel/", admin_panel, name="admin_panel"),
    path("profile/", profile, name="profile"),
    path("profile/<int:user_id>/detail/", profile_single, name="profile_single"),
    path("setting/", profile_update, name="edit_profile"),
    path("change_password/", change_password, name="change_password"),
    path("lecturers/", LecturerFilterView.as_view(), name="lecturer_list"),
    path("lecturer/add/", staff_add_view, name="add_lecturer"),
    path("staff/<int:pk>/edit/", edit_staff, name="staff_edit"),
    path("lecturers/<int:pk>/delete/", delete_staff, name="lecturer_delete"),
    path("students/", StudentListView.as_view(), name="student_list"),
    path("student/add/", student_add_view, name="add_student"),
    path("student/<int:pk>/edit/", edit_student, name="student_edit"),
    path("students/<int:pk>/delete/", delete_student, name="student_delete"),
    path(
        "edit_student_program/<int:pk>/",
        edit_student_program,
        name="student_program_edit",
    ),
    path("ajax/validate-username/", validate_username, name="validate_username"),
    path("register/", register, name="register"),
    # paths to pdf
    path(
        "create_lecturers_pdf_list/", render_lecturer_pdf_list, name="lecturer_list_pdf"
    ),  # new
    path(
        "create_students_pdf_list/", render_student_pdf_list, name="student_list_pdf"
    ), 
]    