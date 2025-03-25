from django.contrib import admin
from .models import FacultyModel, DepartmentModel, CourseModel, StudentModel

class FacultyAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']

class DepartmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']

class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ['students']

class StudentAdmin(admin.ModelAdmin):
    list_display = ['studentID', 'course']

admin.site.register(FacultyModel, FacultyAdmin)
admin.site.register(DepartmentModel, DepartmentAdmin)
admin.site.register(CourseModel, CourseAdmin)
admin.site.register(StudentModel, StudentAdmin)