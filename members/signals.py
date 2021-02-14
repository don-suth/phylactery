from .models import Rank


def populate_ranks(sender, **kwargs):
    # Function here to make sure the Ranks model is populated with all it's choices, and no more.
    rank_choices = list(map(lambda i: i[0], Rank._meta.get_field('rank_name').choices))
    for rank_name in rank_choices:
        if not Rank.objects.filter(rank_name=rank_name).exists():
            Rank.objects.create(rank_name=rank_name)
    for rank in Rank.objects.exclude(rank_name__in=rank_choices):
        rank.delete()


def populate_groups_and_permissions(sender, **kwargs):
    pass
