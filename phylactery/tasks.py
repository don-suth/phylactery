from celery import shared_task
from celery.utils.log import get_task_logger

from django.core.mail import EmailMessage, get_connection

logger = get_task_logger(__name__)


@shared_task(name="send_single_email_task")
def send_single_email_task(email_address, subject, message, unsubscribe_footer=False, connection=None):
    """
        Sends an email to a single email address asynchronously.
    """
    email = EmailMessage(
        subject=subject,
        body=message,
        to=[email_address],
        connection=connection,
    )

    email.send()
    logger.info("Sent email to "+email_address)


@shared_task(name="send_mass_email_task")
def send_mass_email_task(email_addresses, subject, message, unsubscribe_footer=True):
    """
        Sends the same email en masse to a list of emails.
        Intended for mailing list purposes.
    """
    connection = get_connection()
    connection.open()
    for email_address in email_addresses:
        email = EmailMessage(
            subject=subject,
            body=message,
            to=[email_address]
        )
        email.send()
    connection.close()

    logger.info('Sent emails to {0} recipients.'.format(len(email_addresses)))