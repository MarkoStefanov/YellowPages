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

Add faculties, departments and courses in the admin at `/admin/` so new users can pick a course
when registering. Without `EMAIL_HOST_PASSWORD` set, verification codes are printed to the
console instead of being emailed.

## Configuration

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secret key (required outside local development) |
| `DJANGO_DEBUG` | `True` (default) or `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names |
| `EMAIL_HOST_USER` | Gmail address that sends verification codes |
| `EMAIL_HOST_PASSWORD` | Gmail app password for that address |

## Tests

```bash
cd UCLYellowPages
python manage.py test profiles
```
