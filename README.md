# UCL Yellow Pages

A directory for UCL students to share contact details (WhatsApp, Instagram, Discord, email)
with the people on their course, department or faculty. Users sign up with a verified
`@ucl.ac.uk` address, choose who can see their profile, and can see who has viewed it.

## Running locally

```bash
pip install -r requirements.txt
cd UCLYellowPages
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

To try it with fake data, run `python manage.py seed_demo` after `migrate`. It adds UCL-style
faculties and courses, 20 students with a mix of visibility settings, some profile views and an
`admin` superuser; the shared password is `DEMO_PASSWORD` in
`profiles/management/commands/seed_demo.py`. Otherwise, add faculties, departments and courses in
the admin at `/admin/` so new users can pick a course when registering.

## Verification emails

Registering sends a 6-digit code to the student's `@ucl.ac.uk` address. Codes are stored hashed
in the `EmailVerification` table, one row per address, so many people can sign up at once. A code
expires after 5 minutes, locks after 5 wrong guesses, can be re-requested after 60 seconds and is
deleted once used.

To send real emails, copy `UCLYellowPages/.env.example` to `UCLYellowPages/.env` and fill in a
Gmail address and an [app password](https://myaccount.google.com/apppasswords) for it (the
account needs 2-Step Verification turned on). Without `EMAIL_HOST_PASSWORD`, codes are printed
to the server console instead.

## Configuration

Set these as environment variables or in `UCLYellowPages/.env`.

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secret key (required outside local development) |
| `DJANGO_DEBUG` | `True` (default) or `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names |
| `DJANGO_DB_PATH` | SQLite file to use (default `db.sqlite3`) |
| `EMAIL_HOST_USER` | Gmail address that sends verification codes |
| `EMAIL_HOST_PASSWORD` | Gmail app password for that address |

## Tests

```bash
cd UCLYellowPages
python manage.py test profiles
```
