from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, RegexValidator


class Faculty(models.Model):
    name = models.CharField(max_length=100)
    students = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.name


class UserData(models.Model):
    VISIBILITY_CHOICES = [
        ('ALL', 'Visible to all UCL students'),
        ('FACULTY', 'Visible to everyone in the faculty'),
        ('DEPARTMENT', 'Visible to everyone in the department'),
        ('COURSE', 'Visible to everyone in the course'),
        ('PRIVATE', 'Only visible to me'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True)
    whatsapp = models.CharField(max_length=15, blank=True, null=True, validators=[RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Must be valid phone number')])
    instagram = models.CharField(max_length=31, blank=True, null=True, validators=[RegexValidator(
        regex=r'^@?[a-zA-Z0-9._]{1,30}$',
        message='Must be valid Instagram username.')])
    email = models.EmailField(null=True, blank=True)
    discord = models.CharField(max_length=32, blank=True, null=True, validators=[RegexValidator(
        regex=r'^([a-zA-Z0-9_\.]{2,32})(#[0-9]{4})?$',
        message="Enter a valid Discord username. ")])
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    profile_visibility = models.CharField(max_length=100, choices=VISIBILITY_CHOICES, default='COURSE')
    track_profile_views = models.BooleanField(default=True)

    class Meta:
        db_table = "profiles_userdata"

    def save(self, *args, **kwargs):
        if self.course:
            self.course.students.add(self.user)
            self.course.department.students.add(self.user)
            self.course.department.faculty.students.add(self.user)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

    def is_profile_visible_to(self, viewer, viewerData):
        if self.profile_visibility == 'ALL':
            return True

        if viewer == self.user:
            return True

        if self.profile_visibility == 'FACULTY' and viewerData.course.department.faculty == self.course.department.faculty:
            return True

        if self.profile_visibility == 'DEPARTMENT' and viewerData.course.department == self.course.department:
            return True

        if self.profile_visibility == 'COURSE' and viewerData.course == self.course:
            return True

        return False


class Login(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    login_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)


class ProfileView(models.Model):
    profile = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='profile_views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.viewer} => {self.profile}"
