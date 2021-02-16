# A dict of groups to create, keyed to a list
# List is in the format (
#  - (bool) is_staff,
#  - (list) any number of 'add', 'change', 'delete', 'view', permissions for everything but Users, Groups, Ranks, etc.
#  - (list) the same, but for Users, Groups, Ranks, etc.
#  )
# True overrides False on is_staff
GROUPS_TO_CREATE = {
    'President':        [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
    'Vice-President':   [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
    'Secretary':        [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
    'Treasurer':        [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
    'Librarian':        [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
    'Fresher-Rep':      [ True, ['add', 'change', 'delete', 'view'], ['view'] ],
    'OCM':              [ True, ['add', 'change', 'delete', 'view'], ['view'] ],
    'IPP':              [ True, ['add', 'change', 'delete', 'view'], ['view'] ],
    'Committee':        [ False, ['none'], ['none'] ],
    'Gatekeeper':       [ False, ['none'], ['none'] ],
    'Webkeeper':        [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
    'Admin':            [ True, ['add', 'change', 'delete', 'view'], ['add', 'change', 'delete', 'view'] ],
}


def populate_ranks(sender, **kwargs):
    # Makes sure that every rank choice is in the database
    from .models import Rank
    rank_choices = list(map(lambda i: i[0], Rank._meta.get_field('rank_name').choices))
    for rank_name in rank_choices:
        if not Rank.objects.filter(rank_name=rank_name).exists():
            Rank.objects.create(rank_name=rank_name)
    for rank in Rank.objects.exclude(rank_name__in=rank_choices):
        rank.delete()


def populate_groups_and_permissions(sender, **kwargs):
    # Make sure the database has all groups and permissions that we need
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    advanced_models = ['rank', 'rankassignments', 'unigamesuser', 'logentry',
                       'permission', 'group', 'user', 'contenttype', 'session']
    simple_types = ContentType.objects.exclude(
        model__in=advanced_models
    )
    advanced_types = ContentType.objects.filter(
        model__in=advanced_models
    )
    for group_name in GROUPS_TO_CREATE:
        group = Group.objects.get_or_create(name=group_name)[0]
        is_staff, simple_permissions, advanced_permissions = GROUPS_TO_CREATE[group_name]
        simple_q = Q()
        for perm in simple_permissions:
            simple_q |= Q(codename__startswith='{0}_'.format(perm))
        advanced_q = Q()
        for perm in advanced_permissions:
            advanced_q |= Q(codename__startswith='{0}_'.format(perm))
        group.permissions.clear()
        permissions_to_add = Permission.objects.filter(Q(content_type__in=simple_types), simple_q)
        group.permissions.add(*permissions_to_add)
        permissions_to_add = Permission.objects.filter(Q(content_type__in=advanced_types), advanced_q)
        group.permissions.add(*permissions_to_add)
    for group in Group.objects.exclude(name__in=GROUPS_TO_CREATE):
        group.delete()
