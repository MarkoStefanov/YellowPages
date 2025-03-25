from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserData, Settings, ProfileView
from django.contrib.auth import get_user_model

class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user_data = UserData.objects.create(
            user=self.user,
            whatsapp='+1234567890',
            instagram='@testuser',
            email='test@example.com'
        )
        self.settings = Settings.objects.create(
            user=self.user
        )

    def test_user_data_creation(self):
        self.assertEqual(self.user_data.user.username, 'testuser')
        self.assertEqual(self.user_data.whatsapp, '+1234567890')
        self.assertEqual(self.user_data.instagram, '@testuser')
        self.assertEqual(self.user_data.email, 'test@example.com')

    def test_settings_creation(self):
        self.assertEqual(self.settings.user.username, 'testuser')
        self.assertEqual(self.settings.whatsapp_visibility, 'REGISTERED')
        self.assertEqual(self.settings.instagram_visibility, 'REGISTERED')
        self.assertEqual(self.settings.email_visibility, 'REGISTERED')
        self.assertTrue(self.settings.track_profile_views)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user_data = UserData.objects.create(user=self.user)
        self.settings = Settings.objects.create(user=self.user)

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

        # Test registration
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complex_password123',
            'password2': 'complex_password123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Check if UserData and Settings were created
        new_user = User.objects.get(username='newuser')
        self.assertTrue(UserData.objects.filter(user=new_user).exists())
        self.assertTrue(Settings.objects.filter(user=new_user).exists())

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        # Test login
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success

    def test_profile_edit_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile-edit'))
        self.assertEqual(response.status_code, 200)

        # Test profile update
        response = self.client.post(reverse('profile-edit'), {
            'whatsapp': '+1234567890',
            'instagram': '@testuser',
            'email': 'test@example.com',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Verify updates
        user_data = UserData.objects.get(user=self.user)
        self.assertEqual(user_data.whatsapp, '+1234567890')
        self.assertEqual(user_data.instagram, '@testuser')
        self.assertEqual(user_data.email, 'test@example.com')

    def test_search_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

        # Test search functionality
        response = self.client.get(f"{reverse('search')}?q=testuser")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    def test_profile_view_tracking(self):
        viewer = User.objects.create_user(
            username='viewer',
            password='viewerpass123'
        )
        UserData.objects.create(user=viewer)
        Settings.objects.create(user=viewer)

        self.client.login(username='viewer', password='viewerpass123')

        # Search for testuser
        response = self.client.get(f"{reverse('search')}?q=testuser")
        self.assertEqual(response.status_code, 200)

        # Verify profile view was recorded
        profile_views = ProfileView.objects.filter(
            profile=self.user_data,
            viewer=viewer
        )
        self.assertTrue(profile_views.exists())

class PrivacyControlTests(TestCase):
    def setUp(self):
        # Create a profile owner
        self.owner = User.objects.create_user(
            username='owner',
            password='ownerpass123'
        )
        self.owner_data = UserData.objects.create(
            user=self.owner,
            whatsapp='+1234567890',
            instagram='@owner',
            email='owner@example.com'
        )
        self.owner_settings = Settings.objects.create(
            user=self.owner,
            whatsapp_visibility='REGISTERED',
            instagram_visibility='ALL',
            email_visibility='NONE'
        )

        # Create a viewer
        self.viewer = User.objects.create_user(
            username='viewer',
            password='viewerpass123'
        )
        self.viewer_data = UserData.objects.create(user=self.viewer)
        self.viewer_settings = Settings.objects.create(user=self.viewer)

        self.client = Client()

    def test_privacy_settings_anonymous(self):
        # Test anonymous access
        response = self.client.get(f"{reverse('search')}?q=owner")
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_privacy_settings_authenticated(self):
        # Login as viewer
        self.client.login(username='viewer', password='viewerpass123')
        response = self.client.get(f"{reverse('search')}?q=owner")
        self.assertEqual(response.status_code, 200)

        # WhatsApp should be visible (REGISTERED)
        self.assertContains(response, '+1234567890')
        # Instagram should be visible (ALL)
        self.assertContains(response, '@owner')
        # Email should be hidden (NONE)
        self.assertNotContains(response, 'owner@example.com')

    def test_privacy_settings_changes(self):
        # Login as viewer
        self.client.login(username='viewer', password='viewerpass123')

        # Change privacy settings
        self.owner_settings.whatsapp_visibility = 'NONE'
        self.owner_settings.instagram_visibility = 'NONE'
        self.owner_settings.save()

        response = self.client.get(f"{reverse('search')}?q=owner")
        self.assertEqual(response.status_code, 200)

        # Both WhatsApp and Instagram should now be hidden
        self.assertNotContains(response, '+1234567890')
        self.assertNotContains(response, '@owner')
