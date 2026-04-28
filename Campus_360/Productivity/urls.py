from django.urls import path
from . import views

app_name = "Productivity"

urlpatterns = [
    path("meeting/upload", views.meeting_upload, name="meeting_upload"),
    path("meeting/<int:pk>", views.meeting_detail, name="meeting_detail"),
    path("notes/new", views.notes_create, name="notes_create"),
    path("notes", views.notes_list, name="notes_list"),
    path("sentiment", views.sentiment_analyze, name="sentiment_analyze"),
]