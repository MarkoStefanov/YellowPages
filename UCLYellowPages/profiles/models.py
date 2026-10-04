import secrets
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac


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

    def is_profile_visible_to(self, viewer, viewer_data):
        if viewer == self.user or self.profile_visibility == 'ALL':
            return True

        # Every remaining level is scoped to a course, so both sides need one
        if self.course is None or viewer_data.course is None:
            return False

        if self.profile_visibility == 'FACULTY':
            return viewer_data.course.department.faculty_id == self.course.department.faculty_id

        if self.profile_visibility == 'DEPARTMENT':
            return viewer_data.course.department_id == self.course.department_id

        if self.profile_visibility == 'COURSE':
            return viewer_data.course_id == self.course_id

        return False


class Login(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    login_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)


class VerificationError(Exception):
    pass


class EmailVerification(models.Model):
    """The current sign-up code for one email address. Each address has its own row,
    so any number of people can be verifying at the same time."""

    LIFETIME = timedelta(minutes=5)
    RESEND_COOLDOWN = timedelta(seconds=60)
    MAX_ATTEMPTS = 5

    email = models.EmailField(unique=True)
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.email} (expires {self.expires_at:%H:%M:%S})"

    @staticmethod
    def _hash(email, code):
        return salted_hmac('profiles.EmailVerification', f'{email}:{code}').hexdigest()

    @classmethod
    def issue(cls, email):
        """Create a fresh code for email, replacing any previous one, and return it."""
        now = timezone.now()
        cls.objects.filter(expires_at__lte=now).delete()

        existing = cls.objects.filter(email=email).first()
        if existing and now - existing.created_at < cls.RESEND_COOLDOWN:
            wait = cls.RESEND_COOLDOWN - (now - existing.created_at)
            raise VerificationError(
                f"Please wait {int(wait.total_seconds()) + 1} seconds before requesting another code.")

        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        cls.objects.update_or_create(email=email, defaults={
            'code_hash': cls._hash(email, code),
            'created_at': now,
            'expires_at': now + cls.LIFETIME,
            'attempts': 0,
        })
        return code

    @classmethod
    def verify(cls, email, code):
        """Raise VerificationError unless code is the current, unexpired code for email."""
        verification = cls.objects.filter(email=email, expires_at__gt=timezone.now()).first()
        if verification is None:
            raise VerificationError("No valid code for this email. It may have expired, so request a new one.")

        if verification.attempts >= cls.MAX_ATTEMPTS:
            raise VerificationError("Too many incorrect attempts. Request a new code.")

        if not constant_time_compare(cls._hash(email, code or ''), verification.code_hash):
            verification.attempts = models.F('attempts') + 1
            verification.save(update_fields=['attempts'])
            raise VerificationError("Incorrect verification code.")


class ProfileView(models.Model):
    profile = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='profile_views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.viewer} => {self.profile}"
