from django.db import models
from django.utils import timezone
from django.urls import reverse
from members.models import Member, MemberFlag

class BlogPost(models.Model):
    # Blog Post Title + Slug
    title = models.CharField(max_length=200)
    slug_title = models.SlugField(max_length=200, unique=True)

    # A short summary of the post to feature as a preview of the contents
    # on the ListView. Markdown not enabled, and won't be included in the main post.
    short_description = models.CharField(max_length=300)

    # The author of the post.
    author = models.CharField(max_length=200)

    # The date at which the post shall be published.
    # If this is in the future, post is hidden.
    publish_on = models.DateTimeField(blank=True, null=True)

    # Body of the post, markdown enabled.
    body = models.TextField(blank=True)

    @property
    def is_published(self):
        if self.publish_on is None:
            return False
        elif self.publish_on > timezone.now():
            return False
        else:
            return True

    @property
    def get_pretty_timestamp(self):
        # Returns a string of when this post was published
        # (or when it will be published)
        if self.is_published:
            now = timezone.now()
            days_difference = (now.date() - self.publish_on.date()).days
            if days_difference == 0:
                # If published today:
                return 'Today'
            elif days_difference == 1:
                # If published yesterday:
                return 'Yesterday'
            elif (days_difference > 1) and (days_difference < 7):
                return '{0} days ago'.format(days_difference)
            else:
                return self.publish_on.date().strftime('%d/%m/%y')
        else:
            if self.publish_on is None:
                return 'Not published'
            else:
                return self.publish_on.date().strftime('Set to be published: %d/%m/%y')

    def __str__(self):
        if self.is_published:
            return self.title
        else:
            return self.title + " (not published)"

    def get_absolute_url(self):
        return reverse('blog:detail-slug', args=[self.slug_title])


class EmailOrder(models.Model):
    # A model that tracks an 'order' for an email to be submitted.
    # A celery task will check these every so often, and send any pending email requests.
    # For an email to be sent, the publish date of the blog post has to be in the past.

    # Track whether we've sent an email or not.
    email_sent = models.BooleanField(default=False)

    # The post for which the order is for
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='emailorders')

    # Which membership flags (if any) to send the emails to. If none, it sends to all members by default.
    # Note: Members will not be sent emails unless they have the "receive emails" flag set to True on their account.
    flags = models.ManyToManyField(MemberFlag, related_name='emailorders')

    @property
    def is_ready(self):
        # Returns true if the post is published and the emails have not been sent.
        return self.email_sent is False and self.post.is_published is True

    def get_members_to_send_to(self):
        qs = Member.objects.none()
        if self.flags.count() == 0:
            # All members that have the receive_email setting set to true.
            qs = Member.objects.filter(receive_emails=True)
        else:
            qs = Member.objects.filter(flags__emailorders=self, receive_emails=True)
        return qs

    def __str__(self):
        return 'Email Order for: {0}'.format(self.post.title)