from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, UpdateView, ListView, CreateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserData, ProfileView, Course
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login as auth_login
from django import forms
import re
from .forms import CustomUserCreationForm, UserDataForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
import json
import secrets
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.http import Http404


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request=request)
        try:
            if form.is_valid():
                user = form.save()
                course = form.cleaned_data['course']

                UserData.objects.create(user=user, course=course)

                auth_login(request, user)
                return redirect('home')
        except forms.ValidationError as e:
            messages.error(request, str(e))
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home')


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserData
    form_class = UserDataForm
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('profile-edit')

    def get_object(self, queryset=None):
        return UserData.objects.get_or_create(user=self.request.user)[0]

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully!')
        return response


class HistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'history.html'
    context_object_name = 'profiles'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            user_profile = UserData.objects.get(user=self.request.user)
            profile_views = ProfileView.objects.filter(profile=user_profile).order_by('-viewed_at')

            context['profile_views'] = profile_views
            context['total_views'] = profile_views.count()
            context['tracking_enabled'] = user_profile.track_profile_views

        except UserData.DoesNotExist:
            context['error'] = "User profile not found"
            context['profile_views'] = []

        return context


class SearchView(LoginRequiredMixin, ListView):
    model = UserData
    template_name = 'search.html'
    context_object_name = 'profiles'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            try:
                viewer_data = UserData.objects.get(user=self.request.user)
            except UserData.DoesNotExist:
                return UserData.objects.none()

            queryset = UserData.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(instagram__icontains=query) |
                Q(whatsapp__icontains=query),
                user__is_active=True
            ).exclude(user=self.request.user)

            # Filter based on profile visibility
            filtered_queryset = [
                profile for profile in queryset
                if profile.is_profile_visible_to(self.request.user, viewer_data)
            ]

            return filtered_queryset
        return UserData.objects.none()


def profile_view(request, username):
    user = get_object_or_404(User, username=username, is_active=True)

    try:
        profile = UserData.objects.get(user=user)
        viewer_data = UserData.objects.get(user=request.user)
    except UserData.DoesNotExist:
        raise Http404("Profile does not exist")

    # Check profile visibility
    if not profile.is_profile_visible_to(request.user, viewer_data) and request.user != user:
        raise Http404("Profile is not visible")

    # Track profile view
    if profile.track_profile_views and request.user != user:
        ProfileView.objects.create(
            profile=profile,  # Ensure this is UserData instance
            viewer=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

    context = {
        'profile': profile,
        'user_profile': user,
        'is_own_profile': request.user == user,
    }

    return render(request, 'profile_detail.html', context)


@csrf_protect
@require_POST
def send_verification_code(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '')

        # Validate email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@ucl\.ac\.uk$', email):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid UCL email address'
            }, status=400)

        # Generate verification code
        verification_code = ''.join(secrets.choice('0123456789') for _ in range(6))

        # Store verification code in session
        request.session['verification_code'] = verification_code
        request.session['verification_email'] = email

        # Send email
        try:
            send_mail(
                'UCL Yellow Pages - Verification Code',
                f'Your verification code is: {verification_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
        except Exception as email_error:
            # Log the email sending error
            print(f"Email sending failed: {email_error}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send verification email'
            }, status=500)

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        # Log the error for debugging
        print(f"Verification code send error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }, status=500)
