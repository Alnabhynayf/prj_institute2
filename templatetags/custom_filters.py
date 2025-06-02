from django import template

register = template.Library()

@register.filter
def accept_count(queryset):
    return queryset.filter(opinion="accept").count()

@register.filter
def reject_count(queryset):
    return queryset.filter(opinion="reject").count()

@register.filter
def multiply(value, arg):
    """ضرب القيمة بالمعامل"""
    return float(value) * float(arg)

# from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


@register.filter
def multiply(value, arg):
    """ضرب القيمة بالمعامل"""
    return float(value) * float(arg)