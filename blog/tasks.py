from celery import shared_task
from celery.utils.log import get_task_logger
from django.template import loader
from phylactery.tasks import send_single_email_task, send_mass_email_task, compose_html_email
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from members.tokens import email_preference_token
import datetime

from .models import EmailOrder

logger = get_task_logger(__name__)


@shared_task(name='send_pending_email_orders_task')
def send_pending_email_order_task():
    """
        Scheduled task.
        Checks the list of email orders, and sends any that:
            a) Haven't been sent, and
            b) Their associated blog post has been published.
        Intended to be run fairly frequently, every 15 minutes or so.
    """

    # Find all active email orders
    email_orders = EmailOrder.objects.filter(email_sent=False)
    if len(email_orders) == 0:
        # If there's none, stop now
        return False

    for order in email_orders:
        if order.is_ready:
            email_subject = '{0} - Unigames News'.format(order.post.title)
            members_to_email_to = order.get_members_to_send_to()
            context = {
                'blogpost': order.post
            }
            for member in members_to_email_to:
                context['uid'] = urlsafe_base64_encode(force_bytes(member.pk))
                context['token'] = email_preference_token.make_token(member)
                body, html_body = compose_html_email('blog/email_blog_post.html', context)
                send_single_email_task.delay(
                    member.email_address,
                    email_subject,
                    body,
                    html_message=html_body,
                    log=True
                )
            order.email_sent = True
            order.save()
    return
