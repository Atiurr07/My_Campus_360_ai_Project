from django.contrib import admin
from . models import Resume, Assignment, PlagiarismReport, StudyPlan

# Register your models here.
# 1. This is for a basic register on admin site::
'''
admin.site.register(Resume)
admin.site.register(Assignment)
admin.site.register(PlagiarismReport)
admin.site.register(StudyPlan)
'''


# 2. Create a custome admin pannel for displaying every thing on admin site:::

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "uploaded_file")
    search_fields = ("user__username", "user__email")
    list_filter = ("created_at",)
    ordering= ("-created_at",)

@admin.register(Assignment)
class AssignmnetAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "teacher", "created_at")
    search_fields = ("title", "teacher__username", "teacher__email")
    list_filter =("created_at",)

@admin.register(PlagiarismReport)
class PlagiarismReportAdmin(admin.ModelAdmin):
    list_display = ("id", "score","created_at")
    list_filter =("created_at",)
    ordering = ("-created_at",)

@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    search_fields = ("user__username", "user__email")
    list_filter =("created_at",)
    ordering = ("-created_at",)