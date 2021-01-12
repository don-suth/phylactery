from django.db import models
from django.db.models import Q
from django.urls import reverse
from taggit.managers import TaggableManager
from taggit.models import Tag
from members.models import Member
import datetime
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


class TagParent(models.Model):
    child_tag = models.OneToOneField(Tag, on_delete=models.CASCADE, related_name='parents')
    parent_tag = models.ManyToManyField(Tag, related_name='children')


class Item(models.Model):
    BOOK = 'BK'
    BOARD_GAME = 'BG'
    CARD_GAME = 'CG'
    OTHER = '??'
    ITEM_TYPE_CHOICES = [
        (BOOK, 'Book'),
        (BOARD_GAME, 'Board Game'),
        (CARD_GAME, 'Card Game'),
        (OTHER, 'Other')
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, null=True)
    description = models.TextField(blank=True)
    condition = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    type = models.CharField(max_length=2, choices=ITEM_TYPE_CHOICES)
    is_borrowable = models.BooleanField(default=True)
    high_demand = models.BooleanField(default=False)

    def image_file_name(self, filename):
        filename, dot, extension = filename.rpartition('.')
        return "library/item_images/{0}.{1}".format(self.slug, extension)

    image = models.ImageField(upload_to=image_file_name, null=True)

    def save(self, *args, **kwargs):
        try:
            computed_tags = self.computed_tags.computed_tags
        except ObjectDoesNotExist:
            computed_tags = ItemComputedTags.objects.create(item=self).computed_tags

        try:
            base_tags = self.base_tags.base_tags
        except ObjectDoesNotExist:
            base_tags = ItemBaseTags.objects.create(item=self).base_tags

        computed_tags.set(*base_tags.all(), clear=True)
        super(Item, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('library:detail-slug', args=[self.slug])

    def __str__(self):
        return self.name

    def get_availability_info(self):
        # Returns a dict, containing keys
        # 'in_clubroom', 'is_available', 'expected_availability_date'
        # If is_available is True, or if the item is never borrowable,
        # then expected_availability_date will be None
        # For this, we assume that if you can't borrow an item overnight, then it's not available
        info = {
            'in_clubroom': True,
            'is_available': True,
            'expected_availability_date': None,
        }

        if not self.is_borrowable:
            info['is_available'] = False
            return info

        today = timezone.now()
        next_day = datetime.timedelta(days=1)

        # Check the internal and external records to see if the item is currently borrowed out
        # Only one of these should be the case
        if info['is_available'] is True:
            records = self.borrow_records \
                .filter(date_borrowed__lte=today, date_returned=None) \
                .order_by('-due_date')
            if records.exists():
                info['in_clubroom'] = False
                info['is_available'] = False
                info['expected_availability_date'] = records.first().due_date
        if info['is_available'] is True:
            ext_records = self.ext_borrow_records \
                .exclude(due_date=None) \
                .filter(date_borrowed__lte=today, date_returned=None) \
                .order_by('-due_date')
            if ext_records.exists():
                info['in_clubroom'] = False
                info['is_available'] = False
                info['expected_availability_date'] = ext_records.first().due_date
        if info['is_available'] is True:
            # We also check if an external form is lodged for tomorrow
            tomorrow_ext_records = self.ext_borrow_records \
                .exclude(due_date=None) \
                .filter(requested_borrow_date=today+next_day) \
                .order_by('-due_date')
            if tomorrow_ext_records.exists():
                info['is_available'] = False
                info['expected_availability_date'] = tomorrow_ext_records.first().due_date

        if info['is_available'] is False:
            # We check here to see how the chain of external borrowing forms could affect the due date
            while True:
                qs = self.ext_borrow_records \
                    .exclude(due_date=None) \
                    .filter(Q(requested_borrow_date=info['expected_availability_date'] + next_day)
                            | Q(requested_borrow_date=info['expected_availability_date'])) \
                    .order_by('-due_date')
                if qs.exists() is False:
                    break
                info['expected_availability_date'] = qs.first().due_date

        return info

    @property
    def is_available(self):
        # Returns True if the item is both borrowable and available
        # Otherwise returns False
        if not self.is_borrowable:
            return False
        now = timezone.now()

        # If the item is borrowed, it's not available
        if self.borrow_records.filter(date_borrowed__lte=now, date_returned=None).exists():
            return False
        if self.ext_borrow_records.filter(date_borrowed__lte=now, date_returned=None).exists():
            return False

        # Since external borrowing requires items to be back one day prior,
        # it's also unavailable if that is the case
        tomorrow = now + datetime.timedelta(days=1)
        if self.ext_borrow_records.filter(requested_borrow_date=tomorrow).exists():
            return False
        return True


class ItemBaseTags(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='base_tags')
    base_tags = TaggableManager(blank=True)


class ItemComputedTags(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='computed_tags')
    computed_tags = TaggableManager(blank=True)


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
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='borrow_records')
    date_borrowed = models.DateField(default=timezone.now)
    auth_gatekeeper_borrow = models.ForeignKey(
        Member,
        null=True,
        on_delete=models.SET_NULL,
        related_name='authorised_borrowing'
    )


    def default_due_date():
        return timezone.now() + datetime.timedelta(weeks=2)

    # Due date can be manually set, but is automatically set for two weeks from now
    # (other factors may modify the due date)
    due_date = models.DateField(default=default_due_date)

    # These are filled out upon return of the item
    date_returned = models.DateField(blank=True, null=True, default=None)
    auth_gatekeeper_return = models.ForeignKey(
        Member,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='authorised_returning',
        default=None
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
    requested_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='ext_borrow_records')

    # The librarian approves this by setting the due date
    due_date = models.DateField(blank=True, null=True, default=None)

    # These fields are set when the borrower collects the item
    borrower_name = models.CharField(max_length=200, blank=True)
    auth_gatekeeper_borrow = models.ForeignKey(
        Member,
        blank=True,
        null=True,
        related_name='authorised_borrowing_ext',
        on_delete=models.SET_NULL,
        default=None,
    )
    date_borrowed = models.DateField(blank=True, null=True, default=None)

    # These fields are set when the borrower returns the item
    returner_name = models.CharField(max_length=200, blank=True)
    auth_gatekeeper_return = models.ForeignKey(
        Member,
        blank=True,
        null=True,
        related_name='authorised_returning_ext',
        on_delete=models.SET_NULL,
        default=None,
    )
    date_returned = models.DateField(blank=True, null=True, default=None)

    # Finally, the librarian validates that these items were returned
    verified_returned = models.BooleanField(default=False)
