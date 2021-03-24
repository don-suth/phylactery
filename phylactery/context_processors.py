# This file is so that settings can be imported during template rendering
# Our use for it is enabling easy customisation of the menu bar for the changing dragon theme

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from members.models import switch_to_proxy


def navbar_colour_settings(request):
    return {
        'NAVBAR_THEME': settings.NAVBAR_THEME,
        'NAVBAR_COLOUR': settings.NAVBAR_COLOUR
    }


def unigames_user_processor(request):
    if request.user.is_authenticated:
        new_user = switch_to_proxy(request.user)
        context = {
            'user': new_user,
            'user_groups': list(new_user.groups.values_list('name', flat=True))
        }
        context['librarian_permissions'] = any(
            x in ['Librarian', 'President', 'Vice-President'] for x in context['user_groups']
        )
        return context
    return {}
