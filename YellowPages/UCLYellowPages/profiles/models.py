from django.db import models
from django.contrib.auth.models import User


class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp = models.CharField(max_length=20, blank=True)
    instagram = models.CharField(max_length=50, blank=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_userdata"


class Login(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    login_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)


class FacultyModel(models.Model):
    name = models.CharField(max_length=100)
    students = models.ManyToManyField('StudentProfile', blank=True)

    def __str__(self):
        return self.name


class DepartmentModel(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(FacultyModel, on_delete=models.CASCADE)
    students = models.ManyToManyField('StudentProfile', blank=True)

    def __str__(self):
        return self.name


class CourseModel(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE)
    students = models.ManyToManyField('StudentProfile', blank=True)

    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    VISIBILITY_CHOICES = [
        ('ALL', 'Visible to all UCL Students'),
        ('FACULTY', 'Visible to Faculty'),
        ('DEPARTMENT', 'Visible to Department'),
        ('COURSE', 'Visible to Course-mates'),
        ('PRIVATE', 'Not Visible')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    personal_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    discord = models.CharField(max_length=100, blank=True, null=True)
    linkedin = models.CharField(max_length=200, blank=True, null=True)

    course = models.ForeignKey('CourseModel', on_delete=models.CASCADE, null=True)
    department = models.ForeignKey('DepartmentModel', on_delete=models.CASCADE, null=True)
    faculty = models.ForeignKey('FacultyModel', on_delete=models.CASCADE, null=True)

    profile_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='COURSE')

    def save(self, *args, **kwargs):
        if self.course:
            self.department = self.course.department
        if self.department:
            self.faculty = self.department.faculty
        super().save(*args, **kwargs)

        if self.course:
            self.course.students.add(self)
        if self.department:
            self.department.students.add(self)
        if self.faculty:
            self.faculty.students.add(self)


class ProfileView(models.Model):
    profile = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='profile_views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
