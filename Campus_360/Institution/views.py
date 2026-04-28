from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AttendanceForm, QueueRequestForm, CancleTokenForm, FeedbackForm, EnrollmentForm
from .models import AttendanceRecord, QueueToken, FeedbackEntry, Course, Service
from django.contrib import messages

from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.db.models import Count, Avg, ExpressionWrapper, F, DurationField, Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
import qrcode
from io import BytesIO
from datetime import timedelta
import json

from django.db import transaction, IntegrityError
from django.db.models import Max

# Create your views here.

# ===-----------------Student :: request token --------------------===
# 1. Views for request queue token::
@login_required
def request_queue_token(request):
    if request.method == 'POST':
        form = QueueRequestForm(request.POST)
        if form.is_valid():
            service = form.cleaned_data['service']
            priority = form.cleaned_data.get('priority', False)

            # check daily token limit:: per service
            if service.daily_limit:
                today_count = QueueToken.objects.filter(service=service, created_at__date = timezone.now().date()).count()
                if today_count >= service.daily_limit:
                    messages.error(request, "Daily token limit for this service reached.")
                    return redirect('institution:queue')

            # Generate unique token safely(handle concurrent(miltiple user) requests )
            for attempt in range(3):
                try:
                    with transaction.atomic():
                        # 1st find last token number for this service::
                        last_token = (
                            QueueToken.objects.filter(service=service).aggregate(Max('token_number'))['token_number__max'] or 0
                        )
                        next_token = last_token + 1


                        token = QueueToken.objects.create(service=service, 
                                                        user=request.user, 
                                                        priority=priority,
                                                        token_number= next_token,
                                                        status= QueueToken.STATUS_WAITING,
                                                        )
                    messages.success(request, f"Your token #{token.token_number} for {service.name} has been generated successfully 🎉🎉🎉.....!!")
                    return redirect('institution:queue_status', token_id=token.id)
                except IntegrityError:
                    continue

            messages.error(request, "Something went wrong while generating your token. Please try again. ")
            return redirect('institution:queue')
    else:
        form=QueueRequestForm()
    return render(request, "institution/request_queue.html", {"form": form})


# ==-------- Student:: view token -------------==
# 2. view for showing queue status::
@login_required
def queue_status(request, token_id):
    token = get_object_or_404(QueueToken, pk=token_id, user=request.user)
    # estimate : count waiting tokens
    waiting = QueueToken.objects.filter(
        service=token.service, 
        status__in=[QueueToken.STATUS_WAITING, QueueToken.STATUS_ACTIVE], 
        token_number__lt=token.token_number).count()
    context = {
        'token': token,
        'waiting': waiting,
    }
    # if this is an HTMX request , return snippet
    if request.headers.get('HX-Request') == 'true':
        return render(request, "institution/_token_status_block.html", context)
    return render(request, "institution/queue_status.html", context)

# ==------------ Student :: Cancle the Token ---------------==
@login_required
@require_POST
def cancel_token(request, token_id):
    token = get_object_or_404(QueueToken, pk=token_id, user=request.user)
    if token.status in [QueueToken.STATUS_WAITING]:
        token.cancel()
        messages.success(request, "Your token has been cancelled.!")
    else:
        messages.error(request, "Can not cancle this token....😥😥")
    return redirect('institution:queue')


# ==== ------------- Admin:: View queue(teacher/admin only) ---------

def is_staff_or_teacher(user):
    return user.is_staff or getattr(user, 'is_teacher', False)


# 3. views for admin queue list::
@login_required
@user_passes_test(is_staff_or_teacher)
def admin_queue_list(request):
    # teacher/admin to view
    # Fetch all active services
    services = Service.objects.filter(active=True).order_by('name')

    # For each service , produce tokens grouped(waiting or active)
    service_queues = []
    for s in services:
        tokens = QueueToken.objects.filter(
            service=s, 
            status__in = [QueueToken.STATUS_WAITING, QueueToken.STATUS_ACTIVE]
        ).order_by('token_number')
        service_queues.append((s, tokens))
    return render(request, "institution/queue_admin.html", {"service_queues": service_queues})

# == Admin: server next token for a service ----
@login_required
@user_passes_test(is_staff_or_teacher)
@require_POST
def serve_next(request, service_id):
    service = get_object_or_404(Service, pk=service_id)

    # pick next token: earliest waiting (priority first)
    try:
        token = QueueToken.objects.filter(
            service=service, 
            status=QueueToken.STATUS_WAITING).order_by('-priority', 'token_number').first()
        if token:
            token.mark_active()
            # if later admin can mark served: for simplicity, mark active and return token data
            messages.success(request, f"Token #{token.token_number} is now active.")
        else:
            messages.info(request, "No waiting tokens.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect('institution:queue_admin')


#  ------ Admin: mark token served ------
@login_required
@user_passes_test(is_staff_or_teacher)
@require_POST
def mark_served(request, token_id):
    token = get_object_or_404(QueueToken, pk=token_id)
    token.mark_served(by_user=request.user)
    messages.success(request, f"Token #{token.token_number} marked served.")
    return redirect('institution:queue_admin')

@login_required
@user_passes_test(is_staff_or_teacher)
def analytics_view(request):
    from django.db.models.functions import ExtractHour

    """
    Displays the Queue & Token Analytics Dashboard.
    Shows service performance, peak hours, and time-based trends.
    """

    # Hndle by using date filter::
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    refresh = request.GET.get("refresh")


    # This is the base queryset: Served tokens only, excluding incomplete ones------
    tokens = QueueToken.objects.filter(
        status=QueueToken.STATUS_SERVED,
        started_at__isnull = False,
        served_at__isnull = False
        )

    # Filtering by date::
    if start_date and end_date:
        tokens = tokens.filter(served_at__date__range= [start_date, end_date])
    else:
        # filter default 7 days::
        week_ago = timezone.now().date() - timedelta(days=7)
        tokens = tokens.filter(served_at__date__gte=week_ago)

    # Describe duration (How long each token to serve)::
    # Duration calculation per token
    data = tokens.annotate(
        duration=ExpressionWrapper(F('served_at')- F('started_at'), output_field=DurationField()))

    # Group by service name:: or
    # --- Average time & total tokens by services ----
    avg_by_service = data.values('service__name').annotate(
        avg_duration=Avg('duration'), 
        total=Count('id'))

    # Formate durations in second
    service_perf = [
        {
            'service': x['service__name'], 
            'avg_minutes':round((x['avg_duration'].total_seconds() / 60), 2) if x['avg_duration'] else 0, 
            'total': x['total'],
        } 
        for x in avg_by_service
    ]
    
    peak_data = (
        data.annotate(hour=ExtractHour('served_at'))
        .values('hour')
        .annotate(total=Count('id'))
        .order_by('hour')
    )
    
    peak_hours = [{"hour":x["hour"], "total": x["total"]} for x in peak_data]

    # Overall summary (stats cards) --- 
    total_tokens = QueueToken.objects.count()
    total_served = QueueToken.objects.filter(status=QueueToken.STATUS_SERVED).count()
    total_cancelled = QueueToken.objects.filter(status=QueueToken.STATUS_CANCELLED).count()

    # Now Combine all chart datasets ----- 
    chart_data = {
        "service_perf": service_perf,
        "peak_hours": peak_hours,
        "summary": {
            "total_tokens": total_tokens,
            "total_served": total_served,
            "cancelled": total_cancelled,
        },
    }

    # For AJAX request -> return JSON only
    if refresh:
        return JsonResponse(chart_data, safe=False)

    return render(
        request, 
        "institution/analytics.html",
        {
            "chart_data_json": json.dumps(chart_data),
            "start_date": start_date,
            "end_date": end_date,
        },
    )

# Define a view for downloading analytics report as pdf or csv file:

### ============ **CSV** =================###
import csv

@login_required
@user_passes_test(is_staff_or_teacher)
def export_analytics_csv(request):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="queue_analytics.csv"'

    writer = csv.writer(response)
    writer.writerow(['Service', 'Avg Duration (min)', 'Total Served'])

    served = QueueToken.objects.filter(status=QueueToken.STATUS_SERVED)
    data = served.annotate(
        duration = ExpressionWrapper(F('served_at') - F('started_at'), output_field=DurationField())
    ).values('service__name').annotate(
        avg_duration=Avg('duration'),
        total=Count('id')
    )
    for x in data:
        avg_minutes = x['avg_duration'].total_seconds() / 60 if x['avg_duration'] else 0
        writer.writerow([x['service__name'], f"{avg_minutes: .2f}", x['total']])
    
    return response

### =============== **PDF** ==============###

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

@login_required
@user_passes_test(is_staff_or_teacher)

def export_analytics_pdf(requets):
    """
    Generate a professional anyalitics report in PDF format.
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="queue_analytics_report.pdf"'

    # Noe Setup PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    element = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal = styles["Normal"]

    element.append(Paragraph("📊 Queue & Token Analyticsc Report", title_style))
    element.append(Spacer(1, 12))

    served = QueueToken.objects.filter(status=QueueToken.STATUS_SERVED)
    data = served.annotate(
        duration=ExpressionWrapper(F('served_at') - F('started_at'), output_field=DurationField())
    ).values('service__name').annotate(
        avg_duration=Avg('duration'),
        total=Count('id')
    )

    table_data = ['Service', 'Avg Dduration(min)', 'Total Served']
    for x in data:
        avg_minutes = x['avg_duration'].total_seconds() / 60 if x['avg_duration'] else 0
        table_data.append([x['service__name'], f"{avg_minutes: .2f}", x['total']])

        t = Table(table_data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#007bff")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        element.append(t)
        element.append(Spacer(1,24))
        element.append(Paragraph("Generated by Queue Analytics System © 2025", normal))

        doc.build(element)
        return response

# QR check-in endpoint --- 
# public link scanned by QR (or protected if we choose to require login)
def qr_checkin(request, qr_uuid):
    token = get_object_or_404(QueueToken, qr_uuid=qr_uuid)

    # Security:: Only allow check-in within a time window or require staff pin 
    # For basic:: mark active or served depending on use-case

    token.mark_active()
    return render(request, "institution/qr_checkin_success.html", {"token": token})

def qr_image(request, qr_uuid):
    token = get_object_or_404(QueueToken, qr_uuid=qr_uuid)

    # Build check-in URL
    checkin_url = request.build_absolute_uri(reverse('institution:qr_checkin', args=[str(token.qr_uuid)]))
    img = qrcode.make(checkin_url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return HttpResponse(buf.getvalue(), content_type='image/png')

#  === FCM device registration endpoint (student POST their device token) -----
from django.views.decorators.csrf import csrf_exempt
from .models import QueueToken

@csrf_exempt
@login_required
@require_POST

def register_fcm_token(request):
    # expect JSON: {'fcm_token': "<token>"}
    data = request.POST or request.body

    # simple version via POST form
    fcm_token = request.POST.get('fcm_token') or request.GET.get('fcm_token')
    if not fcm_token:
        return JsonResponse({
            "ok": False,
            "error": "no token"
        }, status=400)
    
    # store in a model MobileDevice 
    from .models import MobileDevice
    device, created = MobileDevice.objects.update_or_create(user=request.user, defaults={'fcm_token': fcm_token})
    return JsonResponse({"ok": True})



# 4.view for attendance admin list::
# Admin can see all attendance records and add new records
def attendance_admin(request):
    if request.user.role != 'admin':
        return redirect("institution:no_permission")  # this is used for safety check
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance record added.")
            return redirect("institution:attendance_admin")
    else:
        form = AttendanceForm()
    records  =AttendanceRecord.objects.select_related('student', 'course').order_by('-date', 'period')[:50]
    return render(request, "institution/attendance_admin.html", {"form": form, "records": records })

# Create an another view to mark the attendance by teacher for their course only::
@login_required
def attendance_teacher(request):
    if request.user.role != 'teacher':
        return redirect("institution:no_permission")
    
    courses = Course.objects.filter(teacher=request.user)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        date = request.POST.get("date")
        period = request.POST.get("period")

        if not (course_id and date and period):
            messages.error(request, "Course , date, and period are required.")
            return redirect("institution:attendance_teacher")

        course = get_object_or_404(Course, id=course_id, teacher=request.user)

        for student in course.student.all():
            status = request.POST.get(f"status_{student.id}")
            if status:
                AttendanceRecord.objects.update_or_create(
                    student=student,
                    course=course,
                    date=date,
                    period=period,
                    defaults={'status': status}
                )
            
        messages.success(request, f"Attendance saved for {course.name} (Period {period})")
        return redirect("institution:attendance_teacher")

    return render(request, "institution/attendance_teacher.html", {'courses': courses})

@login_required
def course_students_api(request, pk):
    try:
        course = Course.objects.get(pk=pk, teacher=request.user)
    except Course.DoesNotExist:
        return JsonResponse({"students": []})

    students = [{"id": s.id, 'username': s.username} for s in course.student.all()]
    return JsonResponse({"students": students})

@login_required
def enroll_students(request):
    if request.user.role not in ["teacher", "admin"]:
        return redirect("institution:no_permission")


    if request.method =="POST":
        form = EnrollmentForm(request.POST, teacher=request.user)
        if form.is_valid():
            course = form.cleaned_data['course']
            students = form.cleaned_data['student']
            course.student.add(*students) # many to many add
            messages.success(request, f"{students.count()} students enrolled in {course.name}.")
            return redirect("institution:enroll_students")
    else:
        form = EnrollmentForm(teacher=request.user)

    return render(request, "institution/enroll_students.html", {"form": form})

@login_required
def attendance_student(request):
    if request.user.role != 'student':
        return redirect('institution:no_permission')

    records = AttendanceRecord.objects.filter(student=request.user).select_related('course').order_by('-date', 'period')[:50]
    total_classes = AttendanceRecord.objects.filter(student=request.user).count()
    attended = AttendanceRecord.objects.filter(student=request.user, status="Present").count()
    attendance_percentage = (attended / total_classes * 100) if total_classes > 0 else 0

    return render(request, "institution/attendance_student.html", {'records': records, 'attendance_percentage': round(attendance_percentage ,2) })

@login_required
def no_permission(request):
    return render(request, "institution/no_permission.html", status=403)


# 5. View for feedback submission and listing
@login_required
def feedback_submit(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.user = request.user
            fb.save()
            messages.success(request, "Thank you for your feedback.")
            return redirect("users:dashboard")
    else:
        form = FeedbackForm()
    return render(request, "institution/feedback_submit.html", {"form": form})
