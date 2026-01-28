from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from .models import NewsAndEvents, ActivityLog, Session, Semester


# ########################################################
# News & Events
# ########################################################
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_date")
    context = {
        "title": "News & Events",
        "items": items,
    }
    return render(request, "core/index.html", context)


@login_required
@admin_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()
    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def post_add(request):
    if request.method == "POST":
        title = request.POST.get("title")
        summary = request.POST.get("summary")
        posted_as = request.POST.get("posted_as")

        if not title or not summary or not posted_as:
            messages.error(request, "All fields are required.")
            return redirect("add_post")

        item = NewsAndEvents.objects.create(
            title=title,
            summary=summary,
            posted_as=posted_as,
        )
        messages.success(request, f"Post '{item.title}' added successfully!")
        return redirect("home")

    return render(request, "core/post_add.html", {"title": "Add Post"})


@login_required
@lecturer_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)

    if request.method == "POST":
        title = request.POST.get("title")
        summary = request.POST.get("summary")
        posted_as = request.POST.get("posted_as")
        picture = request.FILES.get("picture")

        if not title or not summary or not posted_as:
            messages.error(request, "All fields are required.")
        else:
            instance.title = title
            instance.summary = summary
            instance.posted_as = posted_as
            if picture:
                instance.picture = picture
            instance.save()
            messages.success(request, f"{instance.title} has been updated.")
            return redirect("home")

    return render(request, "core/post_add.html", {
        "title": "Edit Post",
        "student": instance,  # optional if template needs it
        "post": instance,
    })

@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    post_title = post.title
    post.delete()
    messages.success(request, f"{post_title} has been deleted.")
    return redirect("home")


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request, pk=None):
    """Add a new session"""
    if pk:
        session = get_object_or_404(Session, pk=pk)
    else:
        session = Session()

    if request.method == "POST":
        session.name = request.POST.get("name")
        session.start_date = request.POST.get("start_date")
        session.end_date = request.POST.get("end_date")
        session.status = request.POST.get("status")

        if not session.name or not session.start_date or not session.end_date:
            messages.error(request, "All fields are required.")
        else:
            session.save()
            messages.success(request, f"Session '{session.name}' saved successfully!")
            return redirect("session_list")

    return render(request, "core/session_update.html", {
        "title": "Session Form",
        "session": session,
    })


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        status = request.POST.get("status")
        is_current_session = request.POST.get("is_current_session")

        # Basic validation
        if not name or not start_date or not end_date:
            messages.error(request, "All fields are required.")
        else:
            session.name = name
            session.start_date = start_date
            session.end_date = end_date
            session.status = status

            # Handle current session toggle
            if is_current_session:
                unset_current_session()  # your helper function
                session.is_current_session = True
            else:
                session.is_current_session = False

            session.save()
            messages.success(request, "Session updated successfully.")
            return redirect("session_list")

    return render(request, "core/session_update.html", {
        "title": "Update Session",
        "session": session,
    })




@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.is_current_session:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted.")
    return redirect("session_list")


def unset_current_session():
    """Unset current session"""
    current_session = Session.objects.filter(is_current_session=True).first()
    if current_session:
        current_session.is_current_session = False
        current_session.save()


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(request, "core/semester_list.html", {"semesters": semesters})


@login_required
@lecturer_required
def semester_add_view(request, pk=None):
    if pk:
        semester = get_object_or_404(Semester, pk=pk)
    else:
        semester = Semester()

#error could arise due to the semester.session foreign key
    if request.method == "POST":
        semester.semester = request.POST.get("semester")
        semester.session = request.POST.get("session")
        semester.next_semester_begins = request.POST.get("next_semester_begins")
        semester.is_current_semester = bool(request.POST.get("is_current_semester"))

        if not semester.semester or not semester.session or not semester.next_semester_begins:
            messages.error(request, "All fields are required.")
        else:
            if semester.is_current_semester:
                unset_current_semester()  # helper to unset previous current semester
            semester.save()
            messages.success(request, f"Semester '{semester.semester}' saved successfully!")
            return redirect("semester_list")

    return render(request, "core/semester_update.html", {
        "title": "Semester Form",
        "semester": semester,
    })

@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)

    if request.method == "POST":
        semester_name = request.POST.get("semester")
        session = request.POST.get("session")
        next_semester_begins = request.POST.get("next_semester_begins")
        is_current_semester = request.POST.get("is_current_semester")

        # Basic validation
        if not semester_name or not session or not next_semester_begins:
            messages.error(request, "All fields are required.")
        else:
            semester.semester = semester_name
            semester.session = session
            semester.next_semester_begins = next_semester_begins

            # Handle current semester toggle
            if is_current_semester:
                unset_current_semester()   # your helper function
                unset_current_session()    # your helper function
                semester.is_current_semester = True
            else:
                semester.is_current_semester = False

            semester.save()
            messages.success(request, "Semester updated successfully!")
            return redirect("semester_list")

    return render(request, "core/semester_update.html", {
        "title": "Update Semester",
        "semester": semester,
    })

@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "You cannot delete the current semester.")
    else:
        semester.delete()
        messages.success(request, "Semester successfully deleted.")
    return redirect("semester_list")


def unset_current_semester():
    """Unset current semester"""
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if current_semester:
        current_semester.is_current_semester = False
        current_semester.save()
