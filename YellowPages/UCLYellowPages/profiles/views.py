from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import RegexValidator
from django.views.generic import TemplateView, UpdateView, ListView, CreateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserData, Settings, ProfileView
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.views.generic import ListView
from .models import UserData
from django.http import Http404
import re
from django import forms


class UCLRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@ucl.ac.uk'):
            raise forms.ValidationError("Registration is only allowed with a UCL email address.")
        return email


class CompleteProfileView(LoginRequiredMixin, UpdateView):
    model = StudentProfile
    form_class = StudentProfileForm
    template_name = 'complete_profile.html'
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        # Create or get existing profile
        profile, created = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile

class SearchView(LoginRequiredMixin, ListView):
    model = StudentProfile
    template_name = 'search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        current_user_profile = StudentProfile.objects.get(user=self.request.user)

        # Base queryset filtering
        queryset = StudentProfile.objects.filter(
            Q(full_name__icontains=query) |
            Q(course__name__icontains=query) |
            Q(department__name__icontains=query)
        ).exclude(user=self.request.user)

        # Apply visibility filters
        filtered_results = []
        for profile in queryset:
            if self.check_visibility(current_user_profile, profile):
                filtered_results.append(profile)

        return filtered_results

    def check_visibility(self, viewer_profile, target_profile):
        # Comprehensive visibility check
        if target_profile.name_visibility == 'ALL':
            return True

        if target_profile.name_visibility == 'FACULTY' and \
           viewer_profile.faculty == target_profile.faculty:
            return True

        if target_profile.name_visibility == 'DEPARTMENT' and \
           viewer_profile.department == target_profile.department:
            return True

        if target_profile.name_visibility == 'COURSE' and \
           viewer_profile.course == target_profile.course:
            return True

        return False


def register(request):
    if request.method == 'POST':
        print("POST request received for registration")
        form = CustomUserCreationForm(request.POST)
        print(f"Form data: {request.POST}")
        print(f"Form is valid: {form.is_valid()}")

        if form.is_valid():
            try:
                # Save the user to the database
                user = form.save()
                print(f"User created: {user.username} (ID: {user.id})")

                # Create the required associated models
                try:
                    user_data = UserData.objects.create(user=user)
                    print(f"UserData created: {user_data.id}")
                except Exception as e:
                    print(f"Error creating UserData: {str(e)}")

                try:
                    settings = Settings.objects.create(user=user)
                    print(f"Settings created: {settings.id}")
                except Exception as e:
                    print(f"Error creating Settings: {str(e)}")

                # Log the user in
                try:
                    auth_login(request, user)
                    print("User logged in successfully")
                except Exception as e:
                    print(f"Error logging in user: {str(e)}")

                # Redirect to the home page
                return redirect('home')
            except Exception as e:
                print(f"Error in registration process: {str(e)}")
        else:
            print(f"Form errors: {form.errors}")
    else:
        print("GET request received for registration form")
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('profile-edit')

    def get_success_url(self):
        return reverse_lazy('home')


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserData
    template_name = 'edit_profile.html'
    fields = ['whatsapp', 'instagram', 'email']
    success_url = reverse_lazy('profile-edit')

    def get_object(self, queryset=None):
        return UserData.objects.get_or_create(user=self.request.user)[0]


class SettingsView(LoginRequiredMixin, UpdateView):
    model = Settings
    template_name = 'settings.html'
    fields = ['whatsapp_visibility', 'instagram_visibility', 'email_visibility', 'track_profile_views']
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return Settings.objects.get_or_create(user=self.request.user)[0]


class HistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = get_object_or_404(UserData, user=self.request.user)
        context['profile_views'] = ProfileView.objects.filter(profile=user_profile).order_by('-viewed_at')
        return context


class SearchView(LoginRequiredMixin, ListView):
    model = UserData
    template_name = 'search.html'
    context_object_name = 'profiles'
    paginate_by = 10  # Show 10 profiles per page

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            queryset = UserData.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(instagram__icontains=query) |
                Q(whatsapp__icontains=query),
                user__is_active=True
            ).exclude(user=self.request.user)

            print(f"Query found {queryset.count()} results")
            return queryset
        return UserData.objects.none()  # Return empty queryset if no query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for profile in context['profiles']:
            settings = Settings.objects.get(user=profile.user)
            profile.visible_fields = {
                'whatsapp': settings.whatsapp_visibility == 'ALL' or
                            (settings.whatsapp_visibility == 'REGISTERED' and self.request.user.is_authenticated),
                'instagram': settings.instagram_visibility == 'ALL' or
                             (settings.instagram_visibility == 'REGISTERED' and self.request.user.is_authenticated),
                'email': settings.email_visibility == 'ALL' or
                         (settings.email_visibility == 'REGISTERED' and self.request.user.is_authenticated),
            }
            # Only track views if the setting is enabled
            if settings.track_profile_views:
                ProfileView.objects.create(
                    profile=profile,
                    viewer=self.request.user,
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
        return context


def profile_view(request, username):
    """
    Display a user's profile with all visible fields.
    """
    user = get_object_or_404(User, username=username, is_active=True)
    try:
        profile = UserData.objects.get(user=user)
        settings = Settings.objects.get(user=user)
    except (UserData.DoesNotExist, Settings.DoesNotExist):
        raise Http404("Profile does not exist")

    # Determine which fields the viewer can see
    profile.visible_fields = {
        'whatsapp': settings.whatsapp_visibility == 'ALL' or
                    (settings.whatsapp_visibility == 'REGISTERED' and request.user.is_authenticated) or
                    request.user == user,
        'instagram': settings.instagram_visibility == 'ALL' or
                     (settings.instagram_visibility == 'REGISTERED' and request.user.is_authenticated) or
                     request.user == user,
        'email': settings.email_visibility == 'ALL' or
                 (settings.email_visibility == 'REGISTERED' and request.user.is_authenticated) or
                 request.user == user,
    }

    # Track profile view if setting is enabled and viewer is not the profile owner
    if settings.track_profile_views and request.user != user and request.user.is_authenticated:
        ProfileView.objects.create(
            profile=profile,
            viewer=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

    context = {
        'profile': profile,
        'user_profile': user,
        'is_own_profile': request.user == user,
    }

    return render(request, 'profile_detail.html', context)
