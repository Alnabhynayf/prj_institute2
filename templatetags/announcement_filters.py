from django import template

register = template.Library()

@register.filter
def filter_is_public(announcements):
    return [a for a in announcements if a.is_public]

@register.filter
def filter_is_private(announcements):
    return [a for a in announcements if not a.is_public]