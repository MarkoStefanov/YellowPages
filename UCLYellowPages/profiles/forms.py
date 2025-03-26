from django import forms
from .models import Course, UserData
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re

class CustomUserCreationForm(UserCreationForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=True,
        label="Your Course"
    )

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('course',)  # Add course to default fields

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$', username):
            raise forms.ValidationError("Username must be a valid UCL email address")
        return username


class UserDataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure dropdown works correctly
        self.fields['profile_visibility'].widget = forms.Select(
            choices=self.fields['profile_visibility'].choices,
            attrs={'class': 'form-select'}
        )

    class Meta:
        model = UserData
        fields = ['whatsapp', 'instagram', 'email', 'profile_visibility', 'track_profile_views']
        widgets = {
            'profile_visibility': forms.Select(attrs={'class': 'form-select'}),
            'track_profile_views': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }
