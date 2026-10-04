import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Course, EmailVerification, UserData, VerificationError

UCL_EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$'


class CustomUserCreationForm(UserCreationForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=True,
        label="Your Course"
    )
    verification_code = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit verification code'
        })
    )

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('course', 'verification_code')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(UCL_EMAIL_REGEX, username):
            raise forms.ValidationError("Username must be a valid UCL email address")
        return username

    def clean_verification_code(self):
        verification_code = self.cleaned_data.get('verification_code')
        username = self.cleaned_data.get('username')
        if not username:
            # clean_username already reported the problem
            return verification_code

        try:
            EmailVerification.verify(username, verification_code)
        except VerificationError as e:
            raise forms.ValidationError(str(e))
        return verification_code

    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            # The code is single use
            EmailVerification.objects.filter(email=user.username).delete()
        return user


class UserDataForm(forms.ModelForm):
    class Meta:
        model = UserData
        fields = ['name', 'whatsapp', 'instagram', 'email', 'discord', 'profile_visibility', 'track_profile_views']
        widgets = {
            'profile_visibility': forms.Select(attrs={'class': 'form-select'}),
            'track_profile_views': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control'}),
            'discord': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }
