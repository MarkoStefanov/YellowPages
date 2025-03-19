from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import FacultyModel, DepartmentModel, CourseModel, StudentModel, CustomUser


class FacultyAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']


class DepartmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']


class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']


class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_number', 'course']

class CustomUserAdmin(UserAdmin):
    list_display = ('student_number', 'ucl_email', 'is_admin', 'is_staff')
    list_filter = ('is_admin', 'is_staff')
    fieldsets = (
        (None, {'fields': ('student_number', 'ucl_email', 'password')}),
        ('Permissions', {'fields': ('is_admin', 'is_staff')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('student_number', 'ucl_email', 'password1', 'password2', 'is_admin', 'is_staff'),
        }),
    )
    search_fields = ('student_number', 'ucl_email')
    ordering = ('student_number',)
    filter_horizontal = ()

admin.site.register(FacultyModel, FacultyAdmin)
admin.site.register(DepartmentModel, DepartmentAdmin)
admin.site.register(CourseModel, CourseAdmin)
admin.site.register(StudentModel, StudentAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
