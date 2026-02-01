# Create your views here.

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from xhtml2pdf import pisa

from accounts.decorators import admin_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.models import Student, User
from core.models import Semester, Session
from course.models import Course
from result.models import TakenCourse

from .models import LEVEL, Program 
from django.contrib.auth import login

# ########################################################
# Utility Functions
# ########################################################


def render_to_pdf(template_name, context):
    """Render a given template to PDF format."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="profile.pdf"'
    template = render_to_string(template_name, context)
    pdf = pisa.CreatePDF(template, dest=response)
    if pdf.err:
        return HttpResponse("We had some problems generating the PDF")
    return response


# ########################################################
# Authentication and Registration
# ########################################################


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        level_id = request.POST.get("level")
        program_id = request.POST.get("program")

        # Basic validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        # Save extra profile info (assuming you have a Profile model)
        # Example:
        user.profile.address = address
        user.profile.phone = phone
        user.profile.gender = gender

        # Foreign key relations
        if level_id:
            try:
                user.profile.level = Level.objects.get(pk=level_id)
            except Level.DoesNotExist:
                pass

        if program_id:
            try:
                user.profile.program = Program.objects.get(pk=program_id)
            except Program.DoesNotExist:
                pass

        user.profile.save()

        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect("home")

    # GET request → fetch options for dropdowns
    levels = Level.objects.all()
    programs = Program.objects.all()
    return render(request, "registration/register.html", {
        "levels": levels,
        "programs": programs,
    })


# ########################################################
# Profile Views
# ########################################################


@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id, semester=current_semester
        )
        context["courses"] = courses
        return render(request, "accounts/profile.html", context)

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id, course__level=student.level
        )
        context.update(
            {
                "courses": courses,
                "level": student.level,
            }
        )
        return render(request, "accounts/profile.html", context)

    # For superuser or other staff
    staff = User.objects.filter(is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()
    user = get_object_or_404(User, pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=user_id, semester=current_semester
        )
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id, course__level=student.level
        )
        context.update(
            {
                "user_type": "Student",
                "courses": courses,
                "student": student,
            }
        )
    else:
        context["user_type"] = "Superuser"

    if request.GET.get("download_pdf"):
        return render_to_pdf("pdf/profile_single.html", context)

    return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(request, "setting/admin_panel.html", {"title": "Admin Panel"})


# ########################################################
# Settings Views
# ########################################################

@login_required
def profile_update(request):
    if request.method == "POST":
        user = request.user

        # Collect data manually from POST
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        picture = request.FILES.get("picture")

        # Basic validation (you can extend this)
        if not email:
            messages.error(request, "Email is required.")
        else:
            # Update user fields manually
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.gender = gender
            user.phone = phone
            user.address = address

            if picture:
                user.picture = picture

            user.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")

    return render(request, "setting/profile_info_change.html")



@login_required
def account_settings(request):
    user = request.user
    profile = user.profile  # OneToOne relation: Profile(user=User)

    if request.method == "POST":
        # Basic fields from request.POST
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        # File field from request.FILES
        picture = request.FILES.get("picture")

        # Update User model
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Update Profile model
        profile.gender = gender
        profile.phone = phone
        profile.address = address
        if picture:
            profile.picture = picture
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("account_settings")

    return render(request, "setting/profile_info_change.html", {
        "title": "Account Settings",
        "user": user,
        "profile": profile,
    })


@login_required
def change_password(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")

        if not request.user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("change_password")

        if new_password1 != new_password2:
            messages.error(request, "New passwords do not match.")
            return redirect("change_password")

        if len(new_password1) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
            return redirect("change_password")

        # Update password
        request.user.set_password(new_password1)
        request.user.save()

        # Keep user logged in after password change
        update_session_auth_hash(request, request.user)

        messages.success(request, "Password changed successfully!")
        return redirect("account_settings")

    return render(request, "setting/password_change.html", {
        "title": "Change Password",
    })


# ########################################################
# Staff (Lecturer) Views
# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        gender = request.POST.get("gender")

        # Basic validation
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
            return redirect("add_lecturer")

        if User.objects.filter(email=email).exists():
            messages.error(request, "A lecturer with this email already exists.")
            return redirect("add_lecturer")

        # Save lecturer
        lecturer = User.objects.create(
            is_lecturer=True,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            phone=phone,
            gender=gender,
        )

        messages.success(request, f"Lecturer {lecturer.first_name} {lecturer.last_name} added successfully!")
        return redirect("lecturer_list")

    return render(request, "accounts/add_staff.html", {
        "title": "Add Lecturer",
    })


@login_required
@admin_required
def edit_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)

    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        picture = request.FILES.get("picture")

        # Basic validation
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
            return redirect("update_lecturer", lecturer_id=lecturer.id)

        # Prevent duplicate email (except for current lecturer)
        if User.objects.filter(email=email).exclude(pk=lecturer.id).exists():
            messages.error(request, "Another lecturer with this email already exists.")
            return redirect("update_lecturer", lecturer_id=lecturer.id)

        # Update fields
        lecturer.email = email
        lecturer.first_name = first_name
        lecturer.last_name = last_name
        lecturer.gender = gender
        lecturer.phone = phone
        lecturer.address = address

        if picture:
            lecturer.picture = picture

        lecturer.save()

        messages.success(request, f"Lecturer {lecturer.first_name} {lecturer.last_name} updated successfully!")
        return redirect("lecturer_list")

    return render(request, "accounts/edit_lecturer.html", {
        "title": "Update Lecturer",
        "lecturer": lecturer,
    })


@method_decorator([login_required, admin_required], name="dispatch")
class LecturerFilterView(FilterView):
    filterset_class = LecturerFilter
    queryset = User.objects.filter(is_lecturer=True)
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lecturers"
        return context


@login_required
@admin_required
def render_lecturer_pdf_list(request):
    lecturers = User.objects.filter(is_lecturer=True)
    template_path = "pdf/lecturer_list.html"
    context = {"lecturers": lecturers}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="lecturers_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


# ########################################################
# Student Views
# ########################################################


@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        email = request.POST.get("email")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        program_id = request.POST.get("program")
        level_id = request.POST.get("level")

        # Basic validation
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
            return redirect("add_student")

        if User.objects.filter(email=email).exists():
            messages.error(request, "A student with this email already exists.")
            return redirect("add_student")

        # Create student
        student = User(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            email=email,
            address=address,
            phone=phone,
            is_student=True,
        )

        # Foreign key relations
        if program_id:
            try:
                student.program = Program.objects.get(pk=program_id)
            except Program.DoesNotExist:
                pass

        if level_id:
            try:
                student.level = Level.objects.get(pk=level_id)
            except Level.DoesNotExist:
                pass

        student.save()

        messages.success(request, f"Student {student.first_name} {student.last_name} added successfully!")
        return redirect("student_list")

    # GET request → fetch options for dropdowns
    programs = Program.objects.all()
    levels = Level.objects.all()
    return render(request, "accounts/add_student.html", {
        "title": "Add Student",
        "programs": programs,
        "levels": levels,
    })


@login_required
@admin_required
def edit_student(request, pk):
    student = get_object_or_404(User, is_student=True, pk=pk)

    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        picture = request.FILES.get("picture")
        program_id = request.POST.get("program")
        level_id = request.POST.get("level")

        # Basic validation
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
            return redirect("update_student", student_id=student.id)

        # Prevent duplicate email (except for current student)
        if User.objects.filter(email=email).exclude(pk=student.id).exists():
            messages.error(request, "Another student with this email already exists.")
            return redirect("update_student", student_id=student.id)

        # Update fields
        student.email = email
        student.first_name = first_name
        student.last_name = last_name
        student.gender = gender
        student.phone = phone
        student.address = address

        if picture:
            student.picture = picture

        # Foreign key relations
        if program_id:
            try:
                student.program = Program.objects.get(pk=program_id)
            except Program.DoesNotExist:
                pass

        if level_id:
            try:
                student.level = Level.objects.get(pk=level_id)
            except Level.DoesNotExist:
                pass

        student.save()

        messages.success(request, f"Student {student.first_name} {student.last_name} updated successfully!")
        return redirect("student_list")

    # GET request → fetch options for dropdowns
    programs = Program.objects.all()
    levels = Level.objects.all()
    return render(request, "accounts/edit_student.html", {
        "title": "Update Student",
        "student": student,
        "programs": programs,
        "levels": levels,
    })


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    queryset = User.objects.filter(is_student=True)
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context


@login_required
@admin_required
def render_student_pdf_list(request):
    students = User.objects.filter(is_student=True)
    template_path = "pdf/student_list.html"
    context = {"students": students}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="students_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(User, is_student=True, pk=pk)
    full_name = student.student.get_full_name
    student.delete()
    messages.success(request, f"Student {full_name} has been deleted.")
    return redirect("student_list")


@login_required
@admin_required
def edit_student_program(request, pk):
    student = get_object_or_404(User, is_student=True, pk=pk)

    if request.method == "POST":
        program_id = request.POST.get("program")
        if program_id:
            try:
                student.program = Program.objects.get(pk=program_id)
                student.save()
                messages.success(request, f"{student.student.get_full_name}'s program updated successfully!")
                return redirect("student_list")
            except Program.DoesNotExist:
                messages.error(request, "Selected program does not exist.")

    programs = Program.objects.all()
    return render(request, "accounts/edit_student_program.html", {
        "title": "Update Program",
        "student": student,
        "programs": programs,
    })
