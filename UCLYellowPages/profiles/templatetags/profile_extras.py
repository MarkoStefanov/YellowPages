from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def display_name(obj):
    """Name to show for a UserData or a User, falling back to their email."""
    if obj is None:
        return 'Deleted account'
    if isinstance(obj, User):
        try:
            return obj.userdata.name or obj.username
        except User.userdata.RelatedObjectDoesNotExist:
            return obj.username
    return obj.name or obj.user.username


@register.filter
def contact_methods(profile):
    """e.g. "WhatsApp, Instagram, Email" for the details a profile has filled in."""
    methods = [
        ('WhatsApp', profile.whatsapp),
        ('Instagram', profile.instagram),
        ('Discord', profile.discord),
        ('Email', profile.email),
    ]
    return ', '.join(label for label, value in methods if value)
