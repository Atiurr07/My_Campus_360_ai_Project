from django.urls import path
from . import views

app_name = 'institution'

urlpatterns = [
    #  ========== Path for Queue Token Management ==========
    path("queue/request/", views.request_queue_token, name="queue"),
    path("queue/status/<uuid:token_id>/", views.queue_status, name="queue_status"),
    path("queue/cancle/<uuid:token_id>/", views.cancel_token, name="cancel_token"),
    path("queue/admin/", views.admin_queue_list, name="queue_admin"),
    path("queue/admin/server/<int:service_id>/", views.serve_next, name="serve_next"),
    path("queue/admin/markserved/<uuid:token_id>/", views.mark_served, name="mark_served"),
    path("queue/qr/<uuid:qr_uuid>/", views.qr_checkin, name="qr_checkin"),
    path("fcm/register/", views.register_fcm_token, name="register_fcm"),
    path("queue/qr_image/<uuid:qr_uuid>/", views.qr_image, name='qr_image'),
    path("queue/analytics/", views.analytics_view, name= "analytics_view"),

    # Dowloading Analytics report::
    path("analytics/export/csv/", views.export_analytics_csv, name="export_analytics_csv"),
    path("analytics/export/pdf/", views.export_analytics_pdf, name="export_analytics_pdf"),

    # === Path for Attendance Management System =====
    path("attendance/admin/", views.attendance_admin, name="attendance_admin"),
    path("attendance/teacher/", views.attendance_teacher, name="attendance_teacher"),
    path("attendance/my/", views.attendance_student, name="attendance_student"),   # here student view can separately

    path("api/course/<int:pk>/students/", views.course_students_api, name="course_students_api"),
    path("attendance/enroll/", views.enroll_students, name="enroll_students"),

    path("feedback/new/", views.feedback_submit, name="feedback_submit"),
    path("no-permission", views.no_permission, name="no_permission")
]