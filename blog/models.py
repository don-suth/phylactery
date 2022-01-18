from django.db import models
from django.utils import timezone


class BlogPost(models.Model):
    # Blog Post Title + Slug
    title = models.CharField(max_length=200)
    slug_title = models.CharField(max_length=200)

    # A short summary of the post to feature as a preview of the contents
    # on the ListView. Markdown not enabled, and won't be included in the main post.
    short_description = models.CharField(max_length=300)

    # The author of the post.
    author = models.CharField(max_length=200)

    # The date at which the post shall be published.
    # If this is in the future, post is hidden.
    publish_on = models.DateTimeField(blank=True)

    # Body of the post, markdown enabled.
    body = models.TextField(blank=True)

    @property
    def is_published(self):
        return self.publish_on <= timezone.now()
