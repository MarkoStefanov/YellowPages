from django.db import models
from django.contrib.auth.models import User

class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp = models.CharField(max_length=20, blank=True)
    instagram = models.CharField(max_length=50, blank=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_userdata"

class Login(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    login_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

class Settings(models.Model):
    VISIBILITY_CHOICES = [
        ('ALL', 'Visible to Everyone'),
        ('REGISTERED', 'Visible to Registered Users'),
        ('NONE', 'Private')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='REGISTERED')
    instagram_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='REGISTERED')
    email_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='REGISTERED')
    track_profile_views = models.BooleanField(default=True)

class ProfileView(models.Model):
    profile = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='profile_views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)