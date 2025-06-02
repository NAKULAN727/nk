from django import template
import math

register = template.Library()

@register.filter(name='abs')
def absolute(value):
    """Returns the absolute value of a number"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value