from celery import shared_task
from celery.utils.log import get_task_logger
from django.template import loader
from django.core.mail import get_connection
from members.tasks import send_single_email_task
import datetime

from .models import BorrowRecord

logger = get_task_logger(__name__)


@shared_task(name="send_due_date_tomorrow_reminder_task")
def send_due_date_tomorrow_reminder_task():
    """
        Scheduled task.
        Sends a reminder to all borrowers of items due the next day.
        Intended to be run every day.
    """
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    # Find all members with items due tomorrow.
    due_tomorrow = BorrowRecord.objects.filter(
        due_date=tomorrow,
        date_returned__isnull=True,
    )
    if len(due_tomorrow) == 0:
        # No items due, we can stop
        logger.info('No items due, sending no reminders')
        return False

    members_with_items = {}

    for record in due_tomorrow:
        if members_with_items.get(record.borrowing_member, None) is None:
            members_with_items[record.borrowing_member] = []
        members_with_items[record.borrowing_member].append(record)

    connection = get_connection()
    connection.open()
    for member in members_with_items:
        email_subject = 'Unigames - Items Due Tomorrow'
        email_body = loader.render_to_string(
            'library/email_reminder_tomorrow.html', {
                'first_name': member.first_name,
                'due_date': tomorrow,
                'record_list': members_with_items[member]
            }
        )
        email_address = member.email_address
        send_single_email_task(email_address, email_subject, email_body, connection=connection)
    connection.close()
    logger.info('Reminders would be sent here.')
    return


@shared_task(name="send_due_date_today_reminder_task")
def send_due_date_today_reminder_task():
    """
        Scheduled task.
        Sends a reminder to all borrowers of items due today.
        Intended to be run every day.
    """
    today = datetime.date.today()

    # Find all members with items due tomorrow.
    due_today = BorrowRecord.objects.filter(
        due_date=today,
        date_returned__isnull=True,
    )
    if len(due_today) == 0:
        # No items due, we can stop
        logger.info('No items due, sending no reminders')
        return False

    members_with_items = {}

    for record in due_today:
        if members_with_items.get(record.borrowing_member, None) is None:
            members_with_items[record.borrowing_member] = []
        members_with_items[record.borrowing_member].append(record)

    connection = get_connection()
    connection.open()
    for member in members_with_items:
        email_subject = 'Unigames - Items Due Today'
        email_body = loader.render_to_string(
            'library/email_reminder_tomorrow.html', {
                'first_name': member.first_name,
                'due_date': today,
                'record_list': members_with_items[member]
            }
        )
        email_address = member.email_address
        send_single_email_task(email_address, email_subject, email_body, connection=connection)
    connection.close()
    logger.info('Reminders would be sent here.')
    return
