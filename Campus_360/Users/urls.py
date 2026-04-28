from django.urls import path

from . import views
from .views import All_Reports, Student_Dashboard, Teacher_Dashboard, Admin_Dashboard

app_name= "users"

urlpatterns = [
    path("register/",views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("dashboard/", views.dasboard_dispatch, name="dashboard"),
    path("dashboard/student/", Student_Dashboard.as_view(), name="student_dashboard"),
    path("dashboard/teacher/", Teacher_Dashboard.as_view(), name="teacher_dashboard"),
    path("dashboard/admin/", Admin_Dashboard.as_view(), name="admin_dashboard"),

    path ("pending-approval/", views.pending_approval, name="pending_approval"),
    path('select-role/', views.select_role, name='select_role'),
    path('after-google-login/', views.after_google_login, name='after_google_login'),

    path("all-reports/", All_Reports.as_view(), name="all_reports"),

    # Manage Users
    path("manage-users/", views.manage_users, name="manage_users"),
    path("view/<int:pk>/", views.view_user, name="view_user"),
    path("edit/<int:pk>/", views.edit_user, name="edit_user"),
    path("delete/<int:pk>/", views.delete_user, name="delete_user"),

    path("reports/export/csv/", views.export_attendance_csv, name= "export_attendance_csv"),
    path("reports/export/excel/", views.export_attendance_excel, name= "export_attendance_excel"),
    path("reports/export/pdf/", views.export_attendance_pdf, name= "export_attendance_pdf"),
]