from django.contrib import admin
from . models import Course, QueueToken, Service, MobileDevice, AttendanceRecord, FeedbackEntry, PlacementQuestionSuggestion

# Register your models here.

# Make a custome register admin pannel::

@admin.register(QueueToken)
class QueueTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'token_number', 'status', 'created_at', 'priority')
    list_filter = ('service', 'status', 'priority')
    ordering = ('-created_at',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'daily_limit')

@admin.register(MobileDevice)
class MobileDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'fcm_token', 'updated_at')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'period', 'status')
    list_filter = ('status',)
    ordering = ('-status',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'teacher')
    search_fields = ('code', 'name', 'teacher__username')
    ordering = ('-code',)


@admin.register(FeedbackEntry)
class FeedbackEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


admin.site.register(PlacementQuestionSuggestion)