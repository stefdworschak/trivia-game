from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def capitalize(string):
    if isinstance(string, str):
        return ' '.join([s.capitalize() for s in string.split(' ')])
    return string