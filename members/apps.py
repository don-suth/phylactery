from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MembersConfig(AppConfig):
    name = 'members'

    def ready(self):
        from .signals import populate_ranks, populate_groups_and_permissions
        post_migrate.connect(populate_ranks, sender=self)
        post_migrate.connect(populate_groups_and_permissions, sender=self)