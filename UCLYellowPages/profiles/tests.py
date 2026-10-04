import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Course, Department, EmailVerification, Faculty, ProfileView, UserData


class ProfilesTestCase(TestCase):
    password = 'complex_password123'

    @classmethod
    def setUpTestData(cls):
        engineering = Faculty.objects.create(name='Engineering')
        maths = Faculty.objects.create(name='Mathematical & Physical Sciences')
        cs = Department.objects.create(name='Computer Science', faculty=engineering)
        ee = Department.objects.create(name='Electronic Engineering', faculty=engineering)
        physics = Department.objects.create(name='Physics', faculty=maths)
        cls.cs_bsc = Course.objects.create(name='Computer Science BSc', department=cs)
        cls.cs_meng = Course.objects.create(name='Computer Science MEng', department=cs)
        cls.ee_beng = Course.objects.create(name='Electronic Engineering BEng', department=ee)
        cls.physics_bsc = Course.objects.create(name='Physics BSc', department=physics)

    def make_user(self, username, course, **data):
        user = User.objects.create_user(username=username, password=self.password)
        return UserData.objects.create(user=user, course=course, **data)


class VisibilityTests(ProfilesTestCase):
    def setUp(self):
        self.owner = self.make_user('owner@ucl.ac.uk', self.cs_bsc)

    def visible_to(self, course):
        viewer = self.make_user(f'viewer{UserData.objects.count()}@ucl.ac.uk', course)
        return self.owner.is_profile_visible_to(viewer.user, viewer)

    def test_owner_always_sees_own_profile(self):
        self.owner.profile_visibility = 'PRIVATE'
        self.assertTrue(self.owner.is_profile_visible_to(self.owner.user, self.owner))

    def test_levels(self):
        expected = {
            # visibility: (same course, same department, same faculty, other faculty)
            'ALL': (True, True, True, True),
            'FACULTY': (True, True, True, False),
            'DEPARTMENT': (True, True, False, False),
            'COURSE': (True, False, False, False),
            'PRIVATE': (False, False, False, False),
        }
        courses = (self.cs_bsc, self.cs_meng, self.ee_beng, self.physics_bsc)
        for visibility, results in expected.items():
            self.owner.profile_visibility = visibility
            for course, result in zip(courses, results):
                with self.subTest(visibility=visibility, viewer_course=course.name):
                    self.assertEqual(self.visible_to(course), result)

    def test_viewer_without_course(self):
        self.owner.profile_visibility = 'COURSE'
        self.assertFalse(self.visible_to(None))

    def test_save_adds_user_to_course_hierarchy(self):
        user = self.owner.user
        self.assertIn(user, self.cs_bsc.students.all())
        self.assertIn(user, self.cs_bsc.department.students.all())
        self.assertIn(user, self.cs_bsc.department.faculty.students.all())


class AuthViewTests(ProfilesTestCase):
    def test_login(self):
        self.make_user('student@ucl.ac.uk', self.cs_bsc)
        response = self.client.post(reverse('login'), {
            'username': 'student@ucl.ac.uk',
            'password': self.password,
        })
        self.assertRedirects(response, reverse('home'))

    def test_pages_require_login(self):
        for url in (reverse('search'), reverse('history'), reverse('profile-edit'),
                    reverse('profile_detail', args=['someone@ucl.ac.uk'])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_send_verification_code_rejects_non_ucl_email(self):
        response = self.client.post(reverse('send_verification_code'), {'email': 'a@gmail.com'},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def send_code(self, email, client=None):
        """Request a code for email and return (response, code read from the sent email)."""
        response = (client or self.client).post(reverse('send_verification_code'), {'email': email},
                                                content_type='application/json')
        match = re.search(r'code is: (\d{6})', mail.outbox[-1].body) if mail.outbox else None
        return response, match and match.group(1)

    def register(self, email, code, client=None):
        return (client or self.client).post(reverse('register'), {
            'username': email,
            'password1': self.password,
            'password2': self.password,
            'course': self.cs_bsc.pk,
            'verification_code': code,
        })

    def test_register_with_verification_code(self):
        email = 'new@ucl.ac.uk'
        response, code = self.send_code(email)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox[0].to, [email])
        self.assertIn('expires in 5 minutes', mail.outbox[0].body)

        response = self.register(email, code)
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(UserData.objects.get(user__username=email).course, self.cs_bsc)
        # Codes are single use
        self.assertFalse(EmailVerification.objects.filter(email=email).exists())

    def test_code_is_stored_hashed(self):
        _, code = self.send_code('new@ucl.ac.uk')
        self.assertNotIn(code, EmailVerification.objects.get().code_hash)

    def test_register_with_wrong_code_fails(self):
        self.send_code('new@ucl.ac.uk')
        response = self.register('new@ucl.ac.uk', '------')
        self.assertContains(response, 'Incorrect verification code.')
        self.assertFalse(User.objects.filter(username='new@ucl.ac.uk').exists())

    def test_expired_code_is_rejected(self):
        _, code = self.send_code('new@ucl.ac.uk')
        EmailVerification.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.register('new@ucl.ac.uk', code)
        self.assertContains(response, 'It may have expired')
        self.assertFalse(User.objects.filter(username='new@ucl.ac.uk').exists())

    def test_code_expires_after_five_minutes(self):
        before = timezone.now()
        self.send_code('new@ucl.ac.uk')
        expires_at = EmailVerification.objects.get().expires_at
        self.assertAlmostEqual((expires_at - before).total_seconds(), 300, delta=5)

    def test_too_many_wrong_attempts_locks_the_code(self):
        _, code = self.send_code('new@ucl.ac.uk')
        for _ in range(EmailVerification.MAX_ATTEMPTS):
            self.register('new@ucl.ac.uk', '000000' if code != '000000' else '111111')
        response = self.register('new@ucl.ac.uk', code)
        self.assertContains(response, 'Too many incorrect attempts')

    def test_resend_has_cooldown(self):
        self.send_code('new@ucl.ac.uk')
        response, _ = self.send_code('new@ucl.ac.uk')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(mail.outbox), 1)

        # Once the cooldown passes, a new code replaces the old one
        EmailVerification.objects.update(created_at=timezone.now() - EmailVerification.RESEND_COOLDOWN)
        response, new_code = self.send_code('new@ucl.ac.uk')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EmailVerification.objects.count(), 1)
        self.assertRedirects(self.register('new@ucl.ac.uk', new_code), reverse('home'))

    def test_several_people_can_verify_at_once(self):
        a, b = self.client_class(), self.client_class()
        _, code_a = self.send_code('a@ucl.ac.uk', a)
        _, code_b = self.send_code('b@ucl.ac.uk', b)
        self.assertEqual(EmailVerification.objects.count(), 2)

        # Each code only works for its own email, whichever browser submits it
        if code_a != code_b:
            self.assertContains(self.register('a@ucl.ac.uk', code_b, a), 'Incorrect verification code.')
        self.assertRedirects(self.register('b@ucl.ac.uk', code_b, a), reverse('home'))
        self.assertRedirects(self.register('a@ucl.ac.uk', code_a, b), reverse('home'))

    def test_cannot_request_code_for_existing_account(self):
        self.make_user('taken@ucl.ac.uk', self.cs_bsc)
        response, _ = self.send_code('taken@ucl.ac.uk')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(mail.outbox), 0)


class ProfileViewTests(ProfilesTestCase):
    def setUp(self):
        self.owner = self.make_user('owner@ucl.ac.uk', self.cs_bsc, name='Owner', instagram='owner_ig')
        self.viewer = self.make_user('viewer@ucl.ac.uk', self.cs_bsc)
        self.client.login(username='viewer@ucl.ac.uk', password=self.password)

    def test_search_finds_visible_profiles_only(self):
        self.make_user('hidden@ucl.ac.uk', self.physics_bsc, name='Owner Hidden')

        response = self.client.get(reverse('search'), {'q': 'Owner'})
        self.assertEqual([p.pk for p in response.context['profiles']], [self.owner.pk])

    def test_empty_search_lists_everyone_visible(self):
        self.make_user('hidden@ucl.ac.uk', self.physics_bsc, name='Hidden')
        other = self.make_user('other@ucl.ac.uk', self.physics_bsc, name='Other', profile_visibility='ALL')

        response = self.client.get(reverse('search'))
        self.assertEqual({p.pk for p in response.context['profiles']}, {self.owner.pk, other.pk})

    def test_search_matches_course_department_and_faculty(self):
        for query in ('Computer Science BSc', 'computer science', 'engineering'):
            with self.subTest(query=query):
                response = self.client.get(reverse('search'), {'q': query})
                self.assertEqual([p.pk for p in response.context['profiles']], [self.owner.pk])

    def test_viewing_profile_is_recorded_in_history(self):
        url = reverse('profile_detail', args=['owner@ucl.ac.uk'])
        self.assertContains(self.client.get(url), 'owner_ig')
        self.assertTrue(ProfileView.objects.filter(profile=self.owner, viewer=self.viewer.user).exists())

        self.client.login(username='owner@ucl.ac.uk', password=self.password)
        response = self.client.get(reverse('history'))
        self.assertContains(response, 'viewer@ucl.ac.uk')

    def test_viewing_is_not_recorded_when_tracking_disabled(self):
        self.owner.track_profile_views = False
        self.owner.save()
        self.client.get(reverse('profile_detail', args=['owner@ucl.ac.uk']))
        self.assertFalse(ProfileView.objects.exists())

    def test_hidden_profile_returns_404(self):
        self.owner.profile_visibility = 'PRIVATE'
        self.owner.save()
        response = self.client.get(reverse('profile_detail', args=['owner@ucl.ac.uk']))
        self.assertEqual(response.status_code, 404)

    def test_own_profile_shows_edit_link(self):
        response = self.client.get(reverse('profile_detail', args=['viewer@ucl.ac.uk']))
        self.assertContains(response, reverse('profile-edit'))

    def test_edit_profile(self):
        response = self.client.post(reverse('profile-edit'), {
            'name': 'Viewer',
            'instagram': 'viewer_ig',
            'profile_visibility': 'ALL',
            'track_profile_views': 'on',
        })
        self.assertRedirects(response, reverse('profile-edit'))
        self.viewer.refresh_from_db()
        self.assertEqual(self.viewer.instagram, 'viewer_ig')
        self.assertEqual(self.viewer.profile_visibility, 'ALL')
