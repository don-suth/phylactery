from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager
from members.models import Member
import datetime
from django.utils import timezone


class ItemTypes(models.Model):
    type_name = models.CharField(max_length=30)

    def __str__(self):
        return self.type_name


class Item(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, null=True)
    description = models.TextField(blank=True)
    condition = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    type = models.ForeignKey(ItemTypes, on_delete=models.PROTECT)
    tags = TaggableManager()

    def image_file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        return "library/item_images/{0}.{1}".format(self.slug, extension)

    image = models.ImageField(upload_to=image_file_name, null=True)

    def get_absolute_url(self):
        return reverse('library:detail-slug', args=[self.slug])

    def __str__(self):
        return self.name



class BorrowRecord(models.Model):
    # These fields are set upon the item being borrowed
    borrowing_member = models.ForeignKey(
        Member,
        null=True,
        on_delete=models.SET_NULL,
        related_name='borrowed'
    )
    member_address = models.CharField(max_length=200)
    member_phone_number = models.CharField(max_length=20)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    date_borrowed = models.DateField(default=timezone.now)
    auth_gatekeeper_borrow = models.ForeignKey(
        Member,
        null=True,
        on_delete=models.SET_NULL,
        related_name='authorised_borrowing'
    )

    def default_due_date(self):
        return timezone.now() + datetime.timedelta(weeks=2)

    # Due date can be manually set, but is automatically set for two weeks from now
    # (other factors may modify the due date)
    due_date = models.DateField(default=default_due_date)

    # These are filled out upon return of the item
    date_returned = models.DateField(blank=True, default=None)
    auth_gatekeeper_return = models.ForeignKey(
        Member,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='authorised_returning'
    )

    # Finally, the librarian verifies that it was returned
    verified_returned = models.BooleanField(default=False)


class ExternalBorrowingRecord(models.Model):
    # All are required due to the initial form
    applicant_name = models.CharField(max_length=200)
    applicant_org = models.CharField(max_length=200, blank=True)
    event_details = models.TextField()
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    requested_borrow_date = models.DateField()
    requested_item = models.ForeignKey(Item, on_delete=models.CASCADE)

    # The librarian approves this by setting the due date
    due_date = models.DateField(blank=True)

    # These fields are set when the borrower collects the item
    borrower_name = models.CharField(max_length=200, blank=True)
    auth_gatekeeper_borrow = models.ForeignKey(
        Member,
        blank=True,
        null=True,
        related_name='authorised_borrowing_ext',
        on_delete=models.SET_NULL
    )
    borrow_date = models.DateField(blank=True)

    # These fields are set when the borrower returns the item
    returner_name = models.CharField(max_length=200, blank=True)
    auth_gatekeeper_return = models.ForeignKey(
        Member,
        blank=True,
        null=True,
        related_name='authorised_returning_ext',
        on_delete=models.SET_NULL
    )
    return_date = models.DateField(blank=True)

    # Finally, the librarian validates that these items were returned
    verified_returned = models.BooleanField(default=False)