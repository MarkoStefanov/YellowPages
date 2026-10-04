from django.contrib import admin
from .models import Faculty, Department, Course, UserData, ProfileView, EmailVerification


class FacultyAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']


class DepartmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']


class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']


admin.site.register(Faculty, FacultyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(UserData)
admin.site.register(ProfileView)


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at', 'expires_at', 'attempts']
    readonly_fields = ['email', 'code_hash', 'created_at', 'expires_at', 'attempts']
