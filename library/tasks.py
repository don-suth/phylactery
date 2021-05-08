from celery import shared_task
from celery.utils.log import get_task_logger
from django.template import loader
from django.core.mail import get_connection
from members.tasks import send_single_email_task
import datetime

from .models import BorrowRecord

logger = get_task_logger(__name__)


@shared_task(name="send_due_date_reminder_task")
def send_due_date_tomorrow_reminder_task():
    """
        Scheduled task.
        Sends a reminder to all borrowers of items due the next day.
        Intended to be run every day.
    """
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

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
            'library/email_reminder.html', {
                'first_name': member.first_name,
                'today_or_tomorrow': 'tomorrow',
                'due_date': tomorrow,
                'item_list': members_with_items[member]
            }
        )
        email_address = member.email_address
        send_single_email_task(email_address, email_subject, email_body, connection=connection)
    connection.close()
    logger.info('Reminders would be sent here.')
    return
