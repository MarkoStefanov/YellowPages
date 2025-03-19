from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    ucl_email = forms.EmailField(
        label="UCL Email",
        max_length=150,
        help_text="Must be a valid UCL email ending in @ucl.ac.uk.",
    )
    student_number = forms.CharField(
        label="Student Number",
        max_length=8,
        help_text="Must be an 8-digit student number.",
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Enter a strong password.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as above, for verification.",
    )

    class Meta:
        model = CustomUser
        fields = ['student_number', 'ucl_email', 'password1', 'password2']