from django.contrib import admin
from . models import ChatLog, SymptomLog, SleepLog

# Register your models here.
# 1.  This is basic register

'''
admin.site.register(ChatLog)
admin.site.register(SymptomLog)
admin.site.register(SleepLog)
'''

# 2. Making a custome admin register pannel:

@admin.register(ChatLog)
class ChatlogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sentiment', 'created_at')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

@admin.register(SymptomLog)
class SymptomLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'symptoms_text', 'created_at')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

@admin.register(SleepLog)
class SleepLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'sleep_hours', 'quality')
    list_filter = ('quality',)
    ordering = ('-quality',)
