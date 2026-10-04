from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Course, Department, Faculty, ProfileView, UserData


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

    def test_register_with_verification_code(self):
        email = 'new@ucl.ac.uk'
        response = self.client.post(reverse('send_verification_code'), {'email': email},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox[0].to, [email])
        code = self.client.session['verification_code']
        self.assertIn(code, mail.outbox[0].body)

        response = self.client.post(reverse('register'), {
            'username': email,
            'password1': self.password,
            'password2': self.password,
            'course': self.cs_bsc.pk,
            'verification_code': code,
        })
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(UserData.objects.get(user__username=email).course, self.cs_bsc)

    def test_register_with_wrong_code_fails(self):
        self.client.post(reverse('send_verification_code'), {'email': 'new@ucl.ac.uk'},
                         content_type='application/json')
        response = self.client.post(reverse('register'), {
            'username': 'new@ucl.ac.uk',
            'password1': self.password,
            'password2': self.password,
            'course': self.cs_bsc.pk,
            'verification_code': '------',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='new@ucl.ac.uk').exists())


class ProfileViewTests(ProfilesTestCase):
    def setUp(self):
        self.owner = self.make_user('owner@ucl.ac.uk', self.cs_bsc, name='Owner', instagram='owner_ig')
        self.viewer = self.make_user('viewer@ucl.ac.uk', self.cs_bsc)
        self.client.login(username='viewer@ucl.ac.uk', password=self.password)

    def test_search_finds_visible_profiles_only(self):
        self.make_user('hidden@ucl.ac.uk', self.physics_bsc, name='Owner Hidden')

        response = self.client.get(reverse('search'), {'q': 'Owner'})
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
