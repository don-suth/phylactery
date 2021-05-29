from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name="cleanup_permissions_task")
def cleanup_permissions_task():
    """
        Scheduled task.
        Cleans up permissions based on expired ranks.
        Intended to be run every day.
    """
    from .models import Member
    successful = 0
    for member in Member.objects.all():
        if member.sync_permissions():
            successful += 1
    logger.info('Verified the permissions of {0} users.'.format(successful))
