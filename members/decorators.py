from django.contrib.auth.decorators import user_passes_test
from .models import switch_to_proxy


def gatekeeper_required(function=None, login_url=None):
    """
    Decorator for views that checks that the user is a logged in gatekeeper or above, redirecting
    to the log-in page if necessary.
    """
    def gatekeeper_test(u):
        u = switch_to_proxy(u)
        return u.is_authenticated and u.is_gatekeeper

    actual_decorator = user_passes_test(
        gatekeeper_test,
        login_url=login_url,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
