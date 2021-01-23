from django import template

register = template.Library()


@register.filter(name='get_attr')
def get_attr(bound_field, attr=None):
    # Gets the actual object from a bound form for template handling
    value = bound_field.data if bound_field.data is not None else bound_field.form.initial.get(bound_field.name)
    if value is None:
        return ''
    if attr is None:
        return str(value)
    attr_chain = attr.split('.')
    for attr_name in attr_chain:
        if hasattr(value, attr_name):
            value = getattr(value, attr_name)
        else:
            return str(value)
    return str(value)