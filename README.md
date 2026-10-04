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
the admin at `/admin/` so new users can pick a course when registering. Without `EMAIL_HOST_PASSWORD` set, verification codes are printed to the
console instead of being emailed.

## Configuration

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
