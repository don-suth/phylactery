from members.decorators import gatekeeper_required
from members.models import switch_to_proxy
from .forms import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.text import slugify
from django.contrib.auth.models import Group
from django.views.generic import TemplateView
from blog.models import BlogPost
from library.models import Item
from django.utils import timezone


CONTROL_PANEL_FORMS = [
    'PurgeAllGatekeepers',
    'ExpireMemberships',
    'MakeGatekeepers',
    'MakeWebkeepers',
    'CommitteeTransfer',
]


def get_form_class(form_name):
    return globals()[form_name]


def form_factory(form_name, *args, **kwargs):
    try:
        form = globals()[form_name]
        return form(*args, **kwargs)
    except KeyError:
        return None


def get_form_lookup():
    form_lookup = {}
    for control_form in CONTROL_PANEL_FORMS:
        form_lookup[slugify(get_form_class(control_form).form_name)] = control_form
    return form_lookup


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
        form = get_form_class(get_form_lookup().get(form_name, None))
        if form is not None:
            if check_permissions(request, form.form_permissions):
                # We have found a form that matches the name, and they have permissions to use it
                bound_form = form(request.POST)
                if bound_form.is_valid():
                    bound_form.submit(request)
                    return redirect("control-panel")
                else:
                    # The form was not valid, something wasn't right with it.
                    already_rendered.append(form_name)
                    rendered_forms.append(bound_form)
    # Renders all control panel segments that the user has access to
    form_lookup = get_form_lookup()
    for form_slug_name in form_lookup:
        if (form_slug_name not in already_rendered) and \
                (check_permissions(request, get_form_class(form_lookup[form_slug_name]).form_permissions)):
            new_form = form_factory(form_lookup[form_slug_name])
            rendered_forms.append(new_form)
    return render(
        request,
        'phylactery/control_panel.html',
        {'rendered_forms': rendered_forms}
    )


class HomeView(TemplateView):
    template_name = 'phylactery/home.html'
    featured_tag_name = 'Featured'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        featured_items = Item.objects.filter(
            Q(base_tags__base_tags__name__in=[self.featured_tag_name])
        ).distinct().order_by('name')

        most_recent_blogposts = BlogPost.objects.filter(
            publish_on__lte=timezone.now()
        ).order_by('-publish_on')[:3]

        context['featured_items'] = featured_items
        context['recent_blogposts'] = most_recent_blogposts

        return context


class CommitteeView(TemplateView):
    template_name = "phylactery/committee.html"

    NON_OCM_POSITIONS = [
        'President',
        'Vice-President',
        'Treasurer',
        'Secretary',
        'Librarian',
        'Fresher-Rep',
        'IPP',
    ]

    NUMBER_OF_OCMS = 4

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()
        context['member'] = Member.objects.all()
        for position in self.NON_OCM_POSITIONS + ['OCM']:
            # Find the member with the most recent non-expired rank
            context[position.replace('-', '')] = Member.objects.filter(
                Q(ranks__expired_date__gt=today) | Q(ranks__expired_date=None),
                ranks__rank__rank_name=position.upper()
            )
        return context
