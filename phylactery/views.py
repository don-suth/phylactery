from members.decorators import gatekeeper_required
from .forms import PurgeAllGatekeepers, ExpireMemberships
from django.shortcuts import render, redirect

PRESIDENT_CONTROL_PANEL_FORMS = [PurgeAllGatekeepers, ExpireMemberships]
CONTROL_PANEL_FORMS = []


@gatekeeper_required
def control_panel_view(request):
    # Renders all control panel segments that the user has access to
    rendered_forms = []
    for form in PRESIDENT_CONTROL_PANEL_FORMS:
        rendered_forms.append(form())
    return render(request, 'phylactery/control_panel.html', {'rendered_forms': rendered_forms})
