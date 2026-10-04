import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Course, UserData

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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(UCL_EMAIL_REGEX, username):
            raise forms.ValidationError("Username must be a valid UCL email address")
        return username

    def clean_verification_code(self):
        verification_code = self.cleaned_data.get('verification_code')

        # Check if request is available (it should be in the view)
        if not self.request:
            raise forms.ValidationError("Verification request could not be processed.")

        # The code is put in the session by views.send_verification_code
        stored_code = self.request.session.get('verification_code')
        stored_email = self.request.session.get('verification_email')
        username = self.cleaned_data.get('username')

        if not stored_code or not stored_email:
            raise forms.ValidationError("No verification code was sent.")

        if stored_email != username:
            raise forms.ValidationError("Verification code was sent to a different email.")

        if verification_code != stored_code:
            raise forms.ValidationError("Incorrect verification code.")

        # Clear the session after successful verification
        del self.request.session['verification_code']
        del self.request.session['verification_email']

        return verification_code


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
