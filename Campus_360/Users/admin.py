from django.contrib import admin
from .models import MainUser
from django.contrib.auth.admin import UserAdmin

# Register your models here.

# For editing the customuser admin password on admin page
class AdminPanel(UserAdmin):
    list_display =('first_name', 'last_name','email','username', 'role', 'date_joined', 'last_login', 'is_active', 'is_approved')
    list_display_links = ('email', 'first_name', 'last_name', 'username')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ('is_admin', 'is_teacher', 'is_student', 'is_superadmin', 'is_approved')
    fieldsets = ()

    actions = ['approve_teachers']

    def approve_teachers(self, request, queryset):
        queryset.update(is_approved=True)
    approve_teachers.short_description = "Approve selected teachers"

admin.site.register(MainUser, AdminPanel)