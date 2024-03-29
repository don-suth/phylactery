from celery import shared_task
from celery.utils.log import get_task_logger

from django.core.mail import get_connection
from django.core.mail import send_mail, send_mass_mail

from django.template.loader import render_to_string

from django.utils.html import strip_tags

from premailer import transform

from logging import CRITICAL as CRITICAL_LOG
from cssutils import log as css_log

from django.contrib.sites.models import Site

from smtplib import SMTPException

logger = get_task_logger(__name__)


def compose_html_email(template_name, context, request=None):
    """
        Returns an email template, ready-to-email, in both plaintext and html form.
    """
    css_log.setLevel(CRITICAL_LOG)
    context['protocol'] = 'https://'
    context['domain'] = Site.objects.get_current().domain
    html_message = render_to_string(template_name, context, request=request)
    html_message = transform(html_message)
    context['override_base'] = 'phylactery/email_base.txt'
    plaintext_message = render_to_string(template_name, context, request=request)
    plaintext_message = strip_tags(plaintext_message)
    return plaintext_message, html_message


@shared_task(name="send_single_email_task", rate_limit="1/s")
def send_single_email_task(email_address, subject, message, html_message=None, connection=None, log=True):
    """
        Sends an email to a single email address asynchronously.
    """
    if connection is None:
        connection = get_connection()
        connection.open()
    try:
        send_mail(subject, message, None, [email_address], html_message=html_message, connection=connection)
    except SMTPException:
        # Get a new connection and try one more time
        connection = get_connection()
        connection.open()
        send_mail(subject, message, None, [email_address], html_message=html_message, connection=connection)
        connection.close()
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
