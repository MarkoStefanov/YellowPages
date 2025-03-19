from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


# Create your models here.

class FacultyModel(models.Model):
    name = models.CharField(max_length=100)
    students = models.ManyToManyField('StudentModel', blank=True)

    def __str__(self):
        return self.name


class DepartmentModel(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(FacultyModel, on_delete=models.CASCADE)
    students = models.ManyToManyField('StudentModel', blank=True)

    def __str__(self):
        return self.name


class CourseModel(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE)
    students = models.ManyToManyField('StudentModel', blank=True)

    def __str__(self):
        return self.name


class StudentModel(models.Model):
    name = models.CharField(max_length=100, )
    ucl_email = models.EmailField(max_length=150, unique=True, validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$',
        message='Must be a valid UCL email ending in @ucl.ac.uk.')])
    student_number = models.CharField(max_length=8, validators=[RegexValidator(
        regex='^[0-9]{8}$',
        message='Must be valid student ID.',
    )], unique=True)
    course = models.ForeignKey(CourseModel, on_delete=models.CASCADE)
    personal_email = models.EmailField(max_length=150, blank=True, null=True, unique=True, validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        message='Must be a valid email address')])
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True, validators=[RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Must be valid phone number')])
    instagram = models.CharField(max_length=31, blank=True, null=True, unique=True, validators=[RegexValidator(
        regex=r'^@?[a-zA-Z0-9._]{1,30}$',
        message='Must be valid username.')])
    discord = models.CharField(max_length=32, blank=True, null=True, unique=True, validators=[RegexValidator(
        regex=r'^(?!.*\.\.)(?!.*\.$)[a-z0-9._]{2,32}$',
        message='Must be valid discord username.'
    )])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        course = self.course
        department = course.department
        faculty = department.faculty

        course.students.add(self)
        department.students.add(self)
        faculty.students.add(self)

    def __str__(self):
        return f"{self.student_number} - {self.name}"


class CustomUserManager(BaseUserManager):
    def create_user(self, student_number, ucl_email, password=None):
        if not student_number:
            raise ValueError('Student number must be provided')
        if not ucl_email:
            raise ValueError('UCL email must be provided')

        user = self.model(student_number=student_number, ucl_email=self.normalize_email(ucl_email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, student_number, ucl_email, password):
        user = self.create_user(student_number, ucl_email, password)
        user.is_admin = True
        user.is_staff = True
        user.save()
        return user


class CustomUser(AbstractBaseUser):
    ucl_email = models.EmailField(max_length=150, validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$',
        message='Must be a valid UCL email ending in @ucl.ac.uk.')], unique=True)
    student_number = models.CharField(max_length=8, validators=[RegexValidator(
        regex='^[0-9]{8}$',
        message='Must be valid student ID.',
    )], unique=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'student_number'
    REQUIRED_FIELDS = ['ucl_email']

    def __str__(self):
        return self.student_number

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin