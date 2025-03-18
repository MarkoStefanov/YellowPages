from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator


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
    studentID = models.CharField(max_length=8, validators=[RegexValidator(
        regex='^[0-9]{8}$',
        message='Must be valid student ID.',
    )], unique=True)
    course = models.ForeignKey(CourseModel, on_delete=models.CASCADE)
    instagram = models.CharField(max_length=31, blank=True, null=True, validators=[RegexValidator(
        regex=r'^@?[a-zA-Z0-9._]{1,30}$',
        message='Must be valid username.')])
    phone_number = models.CharField(max_length=15, blank=True, null=True, validators=[RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Must be valid phone number')])
    ucl_email = models.CharField(max_length=150, validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$',
        message='Must be a valid UCL email ending in @ucl.ac.uk.')])
    personal_email = models.CharField(max_length=150, blank=True, null=True, validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        message='Must be a valid email address'
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
        return f"{self.studentID} - {self.name}"
