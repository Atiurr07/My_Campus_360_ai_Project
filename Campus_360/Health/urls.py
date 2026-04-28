from django.urls import path
from . import views

app_name = "Health"

urlpatterns = [
    path("chat/", views.chat, name= "chat"),
    path("symptom-check/", views.symptom_check, name= "symptom_check"),
    path("symptom-result/<int:pk>/", views.symptom_result, name= "symptom_result"),
    path("sleep-log/", views.sleep_log, name= "sleep_log"),
]