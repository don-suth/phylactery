from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name="send_activation_email_task")
def send_activation_email_task(email, message):
    """Sends an email when someone wants to activate their account"""
    logger.info("Sent activation email")
    return


@shared_task(name="send_reset_email_task")
def send_reset_email_task(email, message):
    """Sends an email when someone wants to reset their password"""
    logger.info("Sent password reset email")
    return
