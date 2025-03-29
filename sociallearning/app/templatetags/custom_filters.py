from django import template

register = template.Library()

@register.filter
def truncate_username(value, length=7):
    if len(value) > length:
        return value[:length] + ".."
    return value
