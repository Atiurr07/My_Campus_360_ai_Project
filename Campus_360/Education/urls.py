from django.urls import path
from . import views

app_name = "education"

urlpatterns = [
    path("resume/upload", views.upload_and_analyze, name= "upload_and_analyze"),
    path("resume/start_analysis/", views.start_analysis_ajax, name= "start_analysis_ajax"),
    path("resume/analysis_status/<str:task_id>/", views.analysis_status, name= "analysis_status"),
    path("resume/<int:pk>", views.resume_detail, name= "resume_detail"),
    path('resume/<int:pk>/optimize/', views.generate_optimized_resume, name="generate_optimized_resume"),

    # Path for Assignment generation
    path("assignment/upload", views.assignment_upload, name= "assignment_upload"),
    path("assignment/<int:pk>", views.assignment_details, name= "assignment_details"),

    # Path for study-plan substances
    path("education/upload-syllabus/", views.upload_syllabus_view, name= "upload_syllabus_view"),
    path("education/request-plan/", views.request_study_plan_view, name= "request_study_plan"),
    path("education/study-dashboard/", views.study_dashboard, name= "study_dashboard"),
    path("education/qa-gemini/", views.qa_gemini, name= "qa_gemini"),
    path("education/study-plan/<int:plan_id>/json/", views.study_plan_json, name= "study_plan_json"),

    # Teacher url
    path("teacher/assignments/", views.teacher_assignment_list, name="teacher_assignment_list"),
    path("teacher/assignments/<int:assignment_id>/submissions/", views.teacher_assignment_submission, name="teacher_assignment_submission"),
    path("teacher/submission/<int:submission_id>/grade/", views.teacher_grade_submission, name="teacher_grade_submission"),

    path("teacher/assignment/<int:pk>/edit/", views.teacher_edit_assignment, name = "teacher_edit_assignment"),
    path("teacher/assignment/<int:pk>/delete/", views.teacher_delete_assignment, name = "teacher_delete_assignment"),

    # Student url
    path("assignments/", views.student_assignment_list, name="student_assignment_list"),
    path("assignment/submit/<int:assignment_id>/", views.student_submit_assignment, name="student_submit_assignment"),

    # path for AI assistant
    path("api/ai-assistant/", views.ai_assistant_page, name="ai_assistant_page"),
    path("api/ai-assistant/query/", views.assistant_api, name="assistant_api"),
]
