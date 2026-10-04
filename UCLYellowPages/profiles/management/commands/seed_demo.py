import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from profiles.models import Course, Department, Faculty, ProfileView, UserData

# Every demo account (including the admin) uses this password.
DEMO_PASSWORD = 'yellowpages-demo'

FACULTIES = {
    'Engineering Sciences': {
        'Computer Science': ['Computer Science BSc', 'Computer Science MEng'],
        'Electronic & Electrical Engineering': ['Electronic & Electrical Engineering BEng'],
        'Mechanical Engineering': ['Mechanical Engineering MEng'],
    },
    'Mathematical & Physical Sciences': {
        'Mathematics': ['Mathematics BSc', 'Mathematics with Economics BSc'],
        'Physics & Astronomy': ['Physics BSc', 'Astrophysics MSci'],
    },
    'Arts & Humanities': {
        'English Language & Literature': ['English BA'],
        'History': ['History BA'],
    },
}

# (first name, last name, course, visibility, has whatsapp, has instagram, has discord)
STUDENTS = [
    ('Aisha', 'Khan', 'Computer Science BSc', 'ALL', True, True, True),
    ('Ben', 'Okafor', 'Computer Science BSc', 'COURSE', True, False, True),
    ('Chloe', 'Martin', 'Computer Science BSc', 'DEPARTMENT', False, True, True),
    ('Daniel', 'Novak', 'Computer Science MEng', 'FACULTY', True, True, False),
    ('Emily', 'Zhang', 'Computer Science MEng', 'ALL', False, True, True),
    ('Farhan', 'Rahman', 'Computer Science MEng', 'PRIVATE', True, False, False),
    ('Grace', 'Adeyemi', 'Electronic & Electrical Engineering BEng', 'FACULTY', True, True, False),
    ('Hugo', 'Lefevre', 'Electronic & Electrical Engineering BEng', 'ALL', False, False, True),
    ('Isla', 'Murray', 'Mechanical Engineering MEng', 'DEPARTMENT', True, True, False),
    ('Jamal', 'Ibrahim', 'Mechanical Engineering MEng', 'ALL', True, False, True),
    ('Kira', 'Tanaka', 'Mathematics BSc', 'COURSE', False, True, True),
    ('Leo', 'Rossi', 'Mathematics BSc', 'ALL', True, True, False),
    ('Maya', 'Patel', 'Mathematics with Economics BSc', 'FACULTY', True, True, True),
    ('Noah', 'Schmidt', 'Physics BSc', 'ALL', False, True, False),
    ('Olivia', 'Brown', 'Physics BSc', 'DEPARTMENT', True, False, True),
    ('Priya', 'Sharma', 'Astrophysics MSci', 'ALL', True, True, True),
    ('Quentin', 'Dubois', 'English BA', 'COURSE', False, True, False),
    ('Rosa', 'Garcia', 'English BA', 'ALL', True, True, False),
    ('Sam', 'Wilson', 'History BA', 'FACULTY', True, False, True),
    ('Tara', 'Kelly', 'History BA', 'ALL', False, True, True),
]


class Command(BaseCommand):
    help = "Fill the database with fake faculties, courses and students for local demos."

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help="Delete existing demo data before seeding.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            User.objects.filter(username__endswith='.demo@ucl.ac.uk').delete()
            Faculty.objects.filter(name__in=FACULTIES).delete()

        courses = {}
        for faculty_name, departments in FACULTIES.items():
            faculty, _ = Faculty.objects.get_or_create(name=faculty_name)
            for department_name, course_names in departments.items():
                department, _ = Department.objects.get_or_create(name=department_name, faculty=faculty)
                for course_name in course_names:
                    courses[course_name], _ = Course.objects.get_or_create(name=course_name, department=department)

        rng = random.Random(34)
        profiles = []
        for i, (first, last, course_name, visibility, whatsapp, instagram, discord) in enumerate(STUDENTS):
            handle = f'{first}.{last}'.lower()
            username = f'{handle}.demo@ucl.ac.uk'
            user, created = User.objects.get_or_create(username=username, defaults={
                'first_name': first, 'last_name': last,
            })
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            profile, _ = UserData.objects.update_or_create(user=user, defaults={
                'name': f'{first} {last}',
                'course': courses[course_name],
                'profile_visibility': visibility,
                'email': f'{handle}@example.com',
                # 07700 900xxx is Ofcom's range reserved for fiction
                'whatsapp': f'+447700900{100 + i:03d}' if whatsapp else None,
                'instagram': f'{first.lower()}_{last.lower()}' if instagram else None,
                'discord': f'{first.lower()}{last.lower()[:3]}' if discord else None,
            })
            profiles.append(profile)

        if not ProfileView.objects.filter(profile__in=profiles).exists():
            now = timezone.now()
            for profile in profiles:
                for viewer in rng.sample(profiles, 4):
                    if viewer != profile:
                        view = ProfileView.objects.create(profile=profile, viewer=viewer.user,
                                                          ip_address='127.0.0.1')
                        view.viewed_at = now - timedelta(hours=rng.randint(1, 24 * 14))
                        view.save(update_fields=['viewed_at'])

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', DEMO_PASSWORD)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(courses)} courses and {len(profiles)} students "
            f"(log in as e.g. {profiles[0].user.username}; password is DEMO_PASSWORD in profiles/management/commands/seed_demo.py)."
        ))
