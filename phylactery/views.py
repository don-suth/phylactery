from members.decorators import gatekeeper_required
from members.models import switch_to_proxy
from .forms import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.text import slugify
from django.contrib.auth.models import Group


# Permissions for forms.
# Each 'tier' has all permissions from the tiers below it.
# Example: The President could do something with permission 'SL', but the Treasurer could not.

# Each form that we wish to load, plus the permissions of those who can use it
CONTROL_PANEL_FORMS = [
    PurgeAllGatekeepers,
    ExpireMemberships,
    MakeGatekeepers,
    TransferCommittee
]

FORM_LOOKUP = {}
for control_form in CONTROL_PANEL_FORMS:
    FORM_LOOKUP[slugify(control_form.form_name)] = control_form


def check_permissions(request, valid_permissions):
    # Given a request and the valid permissions of a form,
    # Returns True if the user has the required permissions.
    # Returns False otherwise
    if request.user.is_superuser:
        return True
    if request.user.groups.filter(name__in=valid_permissions).exists():
        return True
    return False


@gatekeeper_required
def control_panel_view(request):
    already_rendered = []
    rendered_forms = []
    if request.method == 'POST':
        # Check which form we should be executing
        form_name = request.POST.get('form_slug_name', None)
        form = FORM_LOOKUP.get(form_name, None)
        if form is not None:
            if check_permissions(request, form.form_permissions):
                # We have found a form that matches the name, and they have permissions to use it
                bound_form = form(request.POST)
                if bound_form.is_valid():
                    bound_form.submit(request)
                else:
                    # The form was not valid, something wasn't right with it.
                    already_rendered.append(form_name)
                    rendered_forms.append(bound_form)
    # Renders all control panel segments that the user has access to

    for form_slug_name in FORM_LOOKUP:
        if (form_slug_name not in already_rendered) and \
                (check_permissions(request, FORM_LOOKUP[form_slug_name].form_permissions)):
            rendered_forms.append(FORM_LOOKUP[form_slug_name]())
    return render(
        request,
        'phylactery/control_panel.html',
        {'rendered_forms': rendered_forms}
    )
