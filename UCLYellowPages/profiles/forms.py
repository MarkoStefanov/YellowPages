import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Course, EmailVerification, UserData, VerificationError

UCL_EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$'


class CustomUserCreationForm(UserCreationForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.order_by('name'),
        required=True,
        label="Your Course",
        empty_label="Choose your course"
    )
    verification_code = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '6-digit code',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
        })
    )

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('course', 'verification_code')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'name@ucl.ac.uk', 'autocomplete': 'email'})

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
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Aisha Khan', 'autocomplete': 'name'}),
            'whatsapp': forms.TextInput(attrs={'placeholder': '+447700900123', 'inputmode': 'tel'}),
            'instagram': forms.TextInput(attrs={'placeholder': 'username'}),
            'discord': forms.TextInput(attrs={'placeholder': 'username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
        }
