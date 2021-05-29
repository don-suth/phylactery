from celery import shared_task
from celery.utils.log import get_task_logger

from django.core.mail import EmailMessage, get_connection
from django.core.mail import send_mail, send_mass_mail

logger = get_task_logger(__name__)


@shared_task(name="send_single_email_task")
def send_single_email_task(email_address, subject, message, html_message=None, connection=None, log=True):
    """
        Sends an email to a single email address asynchronously.
    """
    send_mail(subject, message, None, [email_address], html_message=html_message, connection=connection)
    if log:
        logger.info("Sent email to "+email_address)


@shared_task(name="send_mass_email_task")
def send_mass_email_task(email_addresses, subject, message, html_message=None):
    """
        Sends the same email en masse to a list of emails.
        Intended for mailing list purposes.
    """
    connection = get_connection()
    connection.open()
    for email_address in email_addresses:
        send_single_email_task(email_address, subject, message, html_message=html_message, log=False)
    connection.close()

    logger.info('Sent emails to {0} recipients.'.format(len(email_addresses)))
