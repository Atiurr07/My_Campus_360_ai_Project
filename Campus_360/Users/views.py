from time import strftime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView

from .models import MainUser
from Institution.models import AttendanceRecord
from .forms import UserRegistrationForm, LoginForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from.forms import MainUserForm

from django.contrib.auth.mixins import LoginRequiredMixin

from django.db.models import Count
from django.utils.safestring import mark_safe
import json
from django.http import HttpResponse

# Configuration for  downloading attendance file in csv, pdf,or excel form
import csv
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

User = get_user_model()

# Create your views here.

# Allow Role based user:: by using django class-view::
class RoleRequiredMixin(LoginRequiredMixin):
    role = None  # set to either student/teacher/admin

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.role:
            return redirect("users:select_role")
        
        if request.user.role == "teacher" and not request.user.is_approved:
            messages.warning(request, "⏳ Your account is pending for admin approval.")
            return redirect("users:pending_approval")

        if self.role:
            if request.user.role != self.role and request.user.role != "admin":
                raise PermissionDenied("You don't have permission to access this page.")

        return super().dispatch(request, *args, **kwargs)

def pending_approval(request):
    return render(request, "users/pending_approval.html")

# Registration ::
def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data.get('role')

            if role == "admin":
                messages.error(request, "Admin registration is not allowed.")
                return redirect('users:register')

            user = form.save(commit=False)
            user.role = role

            # set boolean flags correcetly::
            user.is_student = False
            user.is_teacher = False
            user.is_admin = False

            # set role based flags::
            if user.role == "student":
                user.is_student = True
                user.is_approved = True  # auto approve student registration
            elif user.role == "teacher":
                user.is_teacher = True
                user.is_approved = False  # Teachers need admin approval

            user.save()

            messages.success(request, "🎉 Registration Successfully! Please Login..!")
            # login(request, user) # if we used this then it's goes directoly to login page without entering any thing because of django inbuilt model
            return redirect('users:login')
        else:
            messages.error(request, "Registration failed....! Try again")
    else:
        form = UserRegistrationForm() 

    return render(request, 'users/register.html', {'form': form})

# login view::
def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['email_or_username']  # can be username or email
            password = form.cleaned_data['password']

            user = None

            # Try login directly (if they entered email and USERNAME_FIELD = 'email')
            user = authenticate(request, username=username_or_email, password=password)

            # If that failed, maybe they entered email instead of username
            # or try to login with email
            if user is None:
                try:
                    user_obj = MainUser.objects.get(username=username_or_email)
                    user = authenticate(request, username=user_obj.email, password=password)
                except MainUser.DoesNotExist:
                    user = None

            if user is not None:
                login(request, user)
                messages.success(request, f"👋 Welcome back {user.username}")
                return redirect("users:dashboard")
            else:
                messages.error(request, "Invalid credentials")
    else:
        form= LoginForm()
    return render(request, "users/login.html", {'form': form})

def after_google_login(request):
    user = request.user

    if not user.role:
        return redirect('users:select_role')
    
    if user.role == "student":
        return redirect('users:dashboard')
    
    elif user.role == "teacher":
        if not user.is_approved:
            return redirect('users:pending_approval')
        return redirect('users:dashboard')

    return redirect('users:dashboard')

# logout::
def user_logout(request):
    logout(request)
    return redirect("users:login")

@login_required
def select_role(request):
    user = request.user

    if request.method == "POST":
        role = request.POST.get("role")

        # 🚫 Prevent admin selection
        if role == "admin":
            messages.error(request, "Invalid role selection.")
            return redirect('users:select_role')

        # Reset flags
        user.is_student = False
        user.is_teacher = False
        user.is_admin = False

        if role == "student":
            user.role = "student"
            user.is_student = True
            user.is_approved = True

        elif role == "teacher":
            user.role = "teacher"
            user.is_teacher = True
            user.is_approved = False  # ⏳ requires approval

        user.save()

        if role == "teacher":
            return redirect('users:pending_approval')

        return redirect('users:dashboard')

    return render(request, "users/select_role.html")

# ============ Now making a dashboard  dispatcher ================

@login_required
def dasboard_dispatch(request):
    if request.user.role == 'student':
        return redirect("users:student_dashboard")
    elif request.user.role == 'teacher':
        return redirect("users:teacher_dashboard")
    elif request.user.role == 'admin':
        return redirect("users:admin_dashboard")
    else:
        return redirect("users:login")

# Role Dashboard::
# 1. student_dashboard::
class Student_Dashboard(RoleRequiredMixin, TemplateView):
    template_name = "users/student_dashboard.html"
    role = "student"


from django.utils.decorators import method_decorator
from Education.models import Assignment, Submission

# 2. teacher_dashboard::
def is_teacher(user):
    return user.is_authenticated and (user.is_teacher or user.role == "teacher")


@method_decorator([login_required, user_passes_test(is_teacher)], name="dispatch")
class Teacher_Dashboard(RoleRequiredMixin, TemplateView):
    """
    Teacher Dashboard (CBV Version)
    - Displays latest assignments created by teacher
    - Displays latest student submissions for those assignments
    """

    template_name = "users/teacher_dashboard.html"
    # role = "teacher"

    def get(self, request, *args, **kwargs):
        # Latest assignment uploaded by this teacher:: 
        assignments = Assignment.objects.filter(
            teacher = request.user
        ).order_by("-created_at")[:5]

        # Latest students submision (for teacher's assignment)
        recent_submissions = Submission.objects.filter(assignment__teacher=request.user).select_related(
            "student", "assignment"
        ).order_by("-submitted_at")[:5]

        context = {
            "assignments": assignments,
            "recent_submissions": recent_submissions,
        }
        return render(request, self.template_name, context)

# 3. student_dashboard::
class Admin_Dashboard(RoleRequiredMixin, TemplateView):
    template_name = "users/admin_dashboard.html"
    role = "admin"

class All_Reports(RoleRequiredMixin, TemplateView):
    template_name = "users/all_reports.html"
    role = "admin"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        student = self.request.GET.get('student')
        teacher = self.request.GET.get('teacher')
        date = self.request.GET.get('date')

        base_qs = AttendanceRecord.objects.all()
        reports = base_qs.order_by('-date')[:50]

        # Apply Filters
        if student:
            base_qs = base_qs.filter(student__username__icontains=student)

        if teacher:
            base_qs = base_qs.filter(teacher__username__icontains=teacher)

        if date:
            base_qs = base_qs.filter(date=date)


        # 1. Quick Stats::
        context["total_records"] = base_qs.count()
        context["unique_students"] = base_qs.values_list("student", flat=True).distinct().count()
        context["unique_teachers"] = base_qs.values_list("teacher", flat=True).distinct().count()
        context["latest_date"] = (base_qs.order_by("-date").first().date if base_qs.exists() else None)

        # Aggregations
        # 2. Count attendance per student (Displaying on Bar Chart)
        student_stats = (
            base_qs.values("student__username")
            .annotate(count= Count("id"))
            .order_by("-count")
        )

        # 3. Count attendance per teacher (Displaying on Pie Chart)
        teacher_stats = (
            base_qs.values("teacher__username")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        teacher_labels = [t["teacher__username"] for t in teacher_stats]
        teacher_counts = [t["count"] for t in teacher_stats]

        context["teacher_labels"] = mark_safe(json.dumps(teacher_labels))
        context["teacher_counts"] = mark_safe(json.dumps(teacher_counts))

        # 4. Attendance Trends (Displaying on line Chart)
        trends = (
            base_qs.values("date")
            .annotate(count = Count("id"))
            .order_by("-date")
        )

        # 5. Top/Max Bottom/Min Students Attendance 
        top_students = student_stats[:5]
        bottom_students = student_stats.order_by("count")[:5]

        # 6. Teacher work load::
        context["teacher_workload_labels"] = teacher_labels
        context["teacher_workload_counts"] = teacher_counts
        context["teacher_workload_total"] = sum(teacher_counts)


        # 7. Alerts (Low attendance students)
        low_attendance_students = [s for s in student_stats if s["count"] < 5]
        context["low_attendance_students"] = low_attendance_students

        # Convert to json data for chart.js
        context["student_labels"] = mark_safe(json.dumps([s["student__username"] for s in student_stats]))
        context["student_counts"] = mark_safe(json.dumps([s["count"] for s in student_stats]))

        context["trend_labels"] = mark_safe(json.dumps([str(t["date"]) for t in trends]))
        context["trend_counts"] = mark_safe(json.dumps([t["count"] for t in trends]))

        context["top_student_labels"] = mark_safe(json.dumps([s["student__username"] for s in top_students]))
        context["top_student_counts"] = mark_safe(json.dumps([s["count"] for s in top_students]))

        context["bottom_student_labels"] = mark_safe(json.dumps([s["student__username"] for s in bottom_students]))
        context["bottom_student_counts"] = mark_safe(json.dumps([s["count"] for s in bottom_students]))

        # filter + reports
        # Report Table
        context['reports'] = reports
        context['filters']= {
            "student": student or "",
            "teacher": teacher or "",
            "date": date or "",
        }
        return context


# Export Csv
def export_attendance_csv(request):
    response = HttpResponse(content_type = "text/csv")
    response["content-Disposition"] = 'attachment; filename="attendance_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Student", "Teacher", "Date", "Status"])

    for record in AttendanceRecord.objects.all().order_by("-date"):
        writer.writerow([record.student.username if record.student else "N/A",
                        record.teacher.username if record.teacher else "N/A",
                        record.date.strftime("%Y-%m-%d") if record.date else "N/A",
                        record.status,
                        ])

    return response

# export  Excel
def export_attendance_excel(request):
    response = HttpResponse(content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["content-Disposition"] = 'attachment; filename="attendance_report.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Records"

    # Header
    ws.append(["Student", "Teacher", "Date", "Status"])

    for record in AttendanceRecord.objects.all().order_by("-date"):
        ws.append([record.student.username if record.student else "N/A",
                    record.teacher.username if record.teacher else "N/A",
                    record.date.strftime("%Y-%m-%d") if record.date else "",
                    record.status
                    ])
    
    wb.save(response)
    return response

# Export PDF
def export_attendance_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["content-Disposition"] = 'attachment; filename="attendance_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph("Attendance Records", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table Data:
    data = [["Student", "Teacher", "Date", "Status"]]
    for record in AttendanceRecord.objects.all().order_by("-date"):
        data.append([record.student.username if record.student else "N/A",
                    record.teacher.username if record.teacher else "N/A",
                    record.date.strftime("%Y-%m-%d") if record.date else "",
                    record.status,
                    ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

# ============ Admin User Management Section ==============
# Admin can manage all users (CRUD)


# 2 things are we need::
# 1. User Profile Information(manage_users)

# 2. User Activity Logs(admin required)
def admin_required(view_func):
    """ Allow only admin user  or a superuser to access this page."""
    return user_passes_test(lambda u: u.is_authenticated and (u.role == 'admin' or u.is_superuser)) (view_func)


# ** Manage Users ** :
@admin_required
def manage_users(request):
    users = MainUser.objects.all().order_by('-date_joined')
    return render(request, 'users/manage_users.html', {'users': users})

@admin_required
def view_user(request, pk):
    user = get_object_or_404(MainUser, pk=pk)
    return render(request, 'users/view_user.html', {'user': user})

@admin_required
def edit_user(request, pk):
    user = get_object_or_404(MainUser, pk=pk)

    if request.method == "POST":
        form = MainUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User details updated successfully.")
            return redirect('users:manage_users')
        else:
            messages.error(request, "Something went wrong. Please correct error below.")
    else:
        form = MainUserForm(instance=user)
    return render(request, 'users/edit_user.html', {'form': form, 'user': user})

@admin_required
def delete_user(request, pk):
    user = get_object_or_404(MainUser, pk=pk)
    if request.method == 'POST':
        if request.user == user:
            messages.error(request, "You can't delete your own account.")
            return redirect('users:manage_users')
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect('users:manage_users')
    return render(request, 'users/delete_user.html', {'user': user})
