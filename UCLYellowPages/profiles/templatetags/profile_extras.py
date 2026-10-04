import zlib

from django import template
from django.contrib.auth.models import User

register = template.Library()


def _name_and_username(obj):
    """Accept a UserData or a User and return (display name or None, username)."""
    if obj is None:
        return None, ''
    if isinstance(obj, User):
        try:
            return obj.userdata.name, obj.username
        except User.userdata.RelatedObjectDoesNotExist:
            return None, obj.username
    return obj.name, obj.user.username


@register.filter
def display_name(obj):
    name, username = _name_and_username(obj)
    return name or username or 'Deleted user'


@register.filter
def initials(obj):
    name, username = _name_and_username(obj)
    words = (name or username.split('@')[0].replace('.', ' ')).split()
    return ''.join(word[0] for word in words[:2]).upper() or '?'


@register.filter
def avatar_hue(obj):
    """A stable colour for each user, so their avatar looks the same everywhere."""
    _, username = _name_and_username(obj)
    return zlib.crc32(username.encode()) % 360
