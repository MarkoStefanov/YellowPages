"""
URL configuration for UCLYellowPages project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from profiles import views as profile_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('profiles/', include('profiles.urls')),
    path('accounts/register/', profile_views.register, name='register'),
    path('accounts/login/', profile_views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', profile_views.custom_logout, name='logout'),
    path('settings/', TemplateView.as_view(template_name='settings.html'), name='settings'),
    path('edit/', TemplateView.as_view(template_name='edit.html'), name='edit'),
    path('history/', TemplateView.as_view(template_name='history.html'), name='history'),
    path('search/', profile_views.SearchView.as_view(), name='search'),
    path('profile/<str:username>/', profile_views.profile_view, name='profile_detail'),
]
