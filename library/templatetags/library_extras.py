from django import template
from library.models import Item

register = template.Library()


@register.filter(name='get_item_attr')
def get_item_attr(bound_field, attr=None):
    # Gets the actual Item object from a bound form for template handling
    value = bound_field.data if bound_field.data is not None else bound_field.form.initial.get(bound_field.name)
    if value is None:
        return ''
    if attr is None:
        return str(value)
    # If we got an int, it's probably the item pk
    if str(value).isdigit():
        qs = Item.objects.filter(pk=value)
        if qs.exists():
            value = qs.first()
    attr_chain = attr.split('.')
    for attr_name in attr_chain:
        if hasattr(value, attr_name):
            value = getattr(value, attr_name)
        else:
            return str(value)
    return str(value)


@register.filter(name='warn_different_due')
def warn_different_due(counter, iterable):
    # Usage: {{ forloop.counter0|warn_different_due=iterable }}
    # Returns iterable[counter]
    counter = int(counter)
    try:
        return iterable[counter]
    except IndexError:
        return ''
