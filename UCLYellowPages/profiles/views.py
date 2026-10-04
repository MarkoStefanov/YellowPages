import json
import logging
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView, UpdateView

from .forms import UCL_EMAIL_REGEX, CustomUserCreationForm, UserDataForm
from .models import EmailVerification, ProfileView, UserData, VerificationError

logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserData.objects.create(user=user, course=form.cleaned_data['course'])

            auth_login(request, user)
            return redirect('home')
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
        query = self.request.GET.get('q', '').strip()

        try:
            viewer_data = UserData.objects.get(user=self.request.user)
        except UserData.DoesNotExist:
            return UserData.objects.none()

        queryset = (UserData.objects.filter(user__is_active=True)
                    .exclude(user=self.request.user)
                    .select_related('user', 'course__department__faculty')
                    .order_by('name', 'user__username'))
        # With no query, list everyone the viewer is allowed to see
        if query:
            queryset = queryset.filter(
                Q(user__username__icontains=query) |
                Q(name__icontains=query) |
                Q(discord__icontains=query) |
                Q(email__icontains=query) |
                Q(instagram__icontains=query) |
                Q(whatsapp__icontains=query) |
                Q(course__name__icontains=query) |
                Q(course__department__name__icontains=query) |
                Q(course__department__faculty__name__icontains=query)
            )

        # Filter based on profile visibility
        return [
            profile for profile in queryset
            if profile.is_profile_visible_to(self.request.user, viewer_data)
        ]


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username, is_active=True)

    try:
        profile = UserData.objects.get(user=user)
        viewer_data = UserData.objects.get(user=request.user)
    except UserData.DoesNotExist:
        raise Http404("Profile does not exist")

    if not profile.is_profile_visible_to(request.user, viewer_data):
        raise Http404("Profile is not visible")

    # Track profile view
    if profile.track_profile_views and request.user != user:
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


@require_POST
def send_verification_code(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)

    email = str(data.get('email', '')).strip()
    if not re.match(UCL_EMAIL_REGEX, email):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid UCL email address'
        }, status=400)

    if User.objects.filter(username__iexact=email).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'An account with this email already exists. Try logging in.'
        }, status=409)

    try:
        verification_code = EmailVerification.issue(email)
    except VerificationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=429)

    minutes = int(EmailVerification.LIFETIME.total_seconds() // 60)
    try:
        send_mail(
            'UCL Yellow Pages - Verification Code',
            f'Your verification code is: {verification_code}\n\n'
            f'It expires in {minutes} minutes.\n\n'
            f'The UCL Yellow Pages team will NEVER ask for any details or send links.',
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", email)
        # Let the user retry straight away rather than waiting out the cooldown
        EmailVerification.objects.filter(email=email).delete()
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to send verification email'
        }, status=500)

    return JsonResponse({'status': 'success'})
