from django.contrib import admin
from .models import Faculty, Department, Course, UserData


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