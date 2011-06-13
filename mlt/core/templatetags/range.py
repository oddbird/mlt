from django import template


register = template.Library()



@register.filter
def range(low, high):
    return xrange(low, high+1)
