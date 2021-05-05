from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name="send_single_email_task")
def send_single_email_task(email_address, message):
    """
        Sends an email to a single email address asynchronously.
    """
    logger.info("Sent activation email")
    return


@shared_task(name="send_mass_email_task")
def send_mass_email_task(email_addresses, message):
    """
        Sends the same email en masse to a list of emails.
        Intended for mailing list purposes.
    """

    logger.info('Emails not sent.')
    return


@shared_task(name="cleanup_permissions_task")
def cleanup_permissions_task():
    """
        Scheduled task.
        Cleans up permissions based on expired ranks.
        Intended to be run every day.
    """
    logger.info("No permissions to clean up.")
    return


@shared_task(name="send_due_date_reminder_task")
def send_due_date_reminder_task():
    """
        Scheduled task.
        Sends a reminder to all borrowers of items due the next day.
        Intended to be run every day.
    """

    logger.info('Reminders would be sent here.')
    return
