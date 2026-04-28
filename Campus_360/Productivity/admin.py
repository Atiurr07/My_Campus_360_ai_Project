from django.contrib import admin
from .models import Meeting, Note, SentimentRecord

# Register your models here.
# 1. This is basics register on admin site::
'''
admin.site.register(Meeting)
admin.site.register(Note)
admin.site.register(SentimentRecord)
'''

# 2. Making a custome register

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'uploaded_at')
    list_filter = ("uploaded_at",)
    ordering= ("-uploaded_at",)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'content', 'created_at')
    list_filter = ("created_at",)
    ordering= ("-created_at",)

@admin.register(SentimentRecord)
class SentimentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'sentiment', 'created_at')
    list_filter = ("created_at",)
    ordering= ("-created_at",)


