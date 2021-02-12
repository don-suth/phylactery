from members.decorators import gatekeeper_required


@gatekeeper_required
def control_panel(request):
    # Control panel view
    pass

