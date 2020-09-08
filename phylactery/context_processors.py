# This file is so that settings can be imported during template rendering
# Our use for it is enabling easy customisation of the menu bar for the changing dragon theme

from django.conf import settings

def admin_colour_settings(request):
    return {
        'NAVBAR_THEME': settings.NAVBAR_THEME,
        'NAVBAR_COLOUR': settings.NAVBAR_COLOUR
    }
