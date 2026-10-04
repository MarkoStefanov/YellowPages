# UCL Yellow Pages

A contact directory for UCL students, built with Django for ENGF0034 (Scenario 2).

Students sign up with their `@ucl.ac.uk` email, add whichever contact details they want to share
(WhatsApp, Instagram, Discord, email), and choose who can see their profile. Other students can
search the directory by name, handle, course, department or faculty, and each student can see who
has viewed their profile.

## Quick start for reviewers

You need Python 3.10+ and nothing else. No email account is needed: without email settings,
verification codes are printed in the terminal running the server.

```bash
git clone https://github.com/MarkoStefanov/YellowPages.git
cd YellowPages
python -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

On Windows use `.venv\Scripts\activate` instead. Then:

```bash
pip install -r requirements.txt
cd UCLYellowPages
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000.

### Demo accounts

`seed_demo` fills the database with fake data: 3 faculties, 10 courses, 20 students with a mix of
privacy settings, and a couple of weeks of profile views. Every demo account uses the password
`yellowpages-demo` (set as `DEMO_PASSWORD` in `profiles/management/commands/seed_demo.py`).

| Log in as | Why it's useful |
| --- | --- |
| `aisha.khan.demo@ucl.ac.uk` | Computer Science BSc. Sees course, department and faculty-only profiles in Engineering, but not other faculties' |
| `priya.sharma.demo@ucl.ac.uk` | Astrophysics MSci, in a different faculty, so sees a different set of people |
| `farhan.rahman.demo@ucl.ac.uk` | Profile set to private, so nobody else can find them |
| `admin` | Superuser for the Django admin at http://127.0.0.1:8000/admin/ |

Running `seed_demo` again is safe. `python manage.py seed_demo --reset` deletes and recreates the
demo data.

## What to try

1. **Sign up.** Go to *Sign up*, enter any `something@ucl.ac.uk` address and click *Send code*.
   The email, including the 6-digit code, appears in the terminal running `runserver`. Enter it,
   pick a course and choose a password. Non-UCL addresses are rejected.
2. **Search.** The search page lists everyone you're allowed to see. Try a name, a course
   (`Computer Science`), a department, a faculty (`Engineering`) or a handle.
3. **Privacy.** Log in as Aisha and search for `Isla` (Mechanical Engineering, department-only):
   no result. Log in as Priya and search for `Maya` (Mathematics with Economics, faculty-only):
   she appears, because they're both in Mathematical & Physical Sciences.
4. **Profile views.** Open someone's profile, then log in as them and open *Views* to see the
   visit. Turning off *Keep a list of who views my profile* stops new visits being recorded.
5. **Edit your profile** under *Profile*. Invalid phone numbers, Instagram or Discord handles are
   rejected with a message.
6. **Light and dark mode.** Use the button at the right of the header. The choice is remembered;
   until you pick one, the site follows your system setting.

## Features

### Visibility rules

Each profile has one visibility level, enforced in `UserData.is_profile_visible_to`
(`profiles/models.py`) and applied to both search results and profile pages:

| Setting | Who can see the profile |
| --- | --- |
| All UCL students | Every logged-in user |
| Faculty | Students whose course is in the same faculty |
| Department | Students whose course is in the same department |
| Course (default) | Students on the same course |
| Private | Only the owner |

Every page except the home, login and sign-up pages requires you to be logged in. A hidden profile
returns a 404, so it can't be told apart from one that doesn't exist.

### Email verification

Sign-up codes are handled by the `EmailVerification` model (`profiles/models.py`):

- One row per email address, so any number of people can verify at the same time.
- Codes are stored as an HMAC hash, never in plain text.
- A code expires after **5 minutes**, locks after **5 wrong attempts**, and can only be
  re-requested after **60 seconds**.
- Codes are single use and deleted once the account is created.
- Requesting a code for an email that already has an account is refused.

## Sending real emails (optional)

Copy `UCLYellowPages/.env.example` to `UCLYellowPages/.env` and fill in a Gmail address and an
[app password](https://myaccount.google.com/apppasswords) for it (the account needs 2-Step
Verification turned on). Restart the server and codes will be emailed instead of printed. `.env`
is ignored by git.

## Configuration

Set these as environment variables or in `UCLYellowPages/.env`:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Secret key; set a real one outside local development | Development-only key |
| `DJANGO_DEBUG` | `True` or `False` | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names | Empty (localhost only) |
| `DJANGO_DB_PATH` | SQLite file to use | `UCLYellowPages/db.sqlite3` |
| `EMAIL_HOST_USER` | Gmail address that sends codes | - |
| `EMAIL_HOST_PASSWORD` | Gmail app password; leave empty to print emails to the console | Empty |

## Tests

```bash
cd UCLYellowPages
python manage.py test profiles
```

There are 24 tests in `profiles/tests.py`. They cover every visibility level, sign-up with valid,
wrong, expired and reused codes, the attempt limit and resend cooldown, two people verifying at
once, search filtering, profile view tracking and editing a profile.

## Project layout

```
UCLYellowPages/
├── manage.py
├── UCLYellowPages/          Project settings and root URLs
├── profiles/                The app
│   ├── models.py            Faculty, Department, Course, UserData, EmailVerification, ProfileView
│   ├── views.py             Home, register, login, search, profile, edit, history, send code
│   ├── forms.py             Sign-up form (UCL email + code check) and profile form
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── templatetags/        display_name and contact_methods template filters
│   └── management/commands/seed_demo.py
├── templates/               Page templates (base.html holds the header and theme toggle)
└── static/                  styles.css, background image, favicon
```

## Team

Built by Marko Stefanov, jude-sph and Fakhrur219. The original feature branches are kept as
`archive/*` tags.
