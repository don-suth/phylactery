from django import template
from library.models import Item
from markdown import Markdown
from io import StringIO

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


# Helper function for the un_markdownify filter
def un_mark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        un_mark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()


Markdown.output_formats["plain"] = un_mark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False


@register.filter(name='un_markdownify')
def un_markdownify(markdown_text):
    # Returns text, without any markdown tags in it
    return __md.convert(markdown_text)
