from django.db import models
from django.db.models import Q
from django.urls import reverse
from taggit.managers import TaggableManager
from taggit.models import Tag
from members.models import Member
import datetime
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

# External Borrowing Form Statuses
UNAPPROVED = 'U'
DENIED = 'D'
APPROVED = 'A'
COMPLETED = 'C'

# Item Types
BOOK = 'BK'
BOARD_GAME = 'BG'
CARD_GAME = 'CG'
OTHER = '??'


def two_weeks_from_now():
    return timezone.now() + datetime.timedelta(weeks=2)


def next_weekday():
    next_day = timezone.now() + datetime.timedelta(days=1)
    while next_day.weekday() not in [0, 1, 2, 3, 4]:
        next_day += datetime.timedelta(days=1)
    return next_day


class TagParent(models.Model):
    child_tag = models.OneToOneField(Tag, on_delete=models.CASCADE, related_name='parents')
    parent_tag = models.ManyToManyField(Tag, related_name='children', blank=True)

    def __str__(self):
        return 'Parents of '+str(self.child_tag)

    def compute_descendant_tags(self):
        # We find all items with the child_tag in their base or computed tags, and re_save them
        for item in Item.objects.filter(
                Q(base_tags__base_tags__name__in=[self.child_tag.name]) |
                Q(computed_tags__computed_tags__name__in=[self.child_tag.name])) \
                .distinct() \
                .order_by('name'):
            item.compute_tags(recursion=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.compute_descendant_tags()



class Item(models.Model):
    """
        Stores a single library item.
    """
    BOOK = BOOK
    BOARD_GAME = BOARD_GAME
    CARD_GAME = CARD_GAME
    OTHER = OTHER
    ITEM_TYPE_CHOICES = [
        (BOOK, 'Book'),
        (BOARD_GAME, 'Board Game'),
        (CARD_GAME, 'Card Game'),
        (OTHER, 'Other')
    ]

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=50, null=True)
    description = models.TextField(blank=True)
    condition = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    type = models.CharField(max_length=2, choices=ITEM_TYPE_CHOICES)
    is_borrowable = models.BooleanField(default=True)
    high_demand = models.BooleanField(default=False)

    min_players = models.IntegerField(blank=True, null=True)
    max_players = models.IntegerField(blank=True, null=True)

    min_play_time = models.IntegerField(blank=True, null=True, help_text='in minutes')
    max_play_time = models.IntegerField(blank=True, null=True, help_text='in minutes')
    average_play_time = models.IntegerField(blank=True, null=True, help_text='in minutes')

    def image_file_name(self, filename):
        filename, dot, extension = filename.rpartition('.')
        return "library/item_images/{0}.{1}".format(self.slug, extension)

    image = models.ImageField(upload_to=image_file_name, null=True)

    class Meta:
        ordering = ['name']

    @property
    def get_base_tags(self):
        """ Returns the base tag TaggableManager, or creates it if it doesn't exist. """
        try:
            base_tags = self.base_tags.base_tags
        except ObjectDoesNotExist:
            base_tags = ItemBaseTags.objects.create(item=self).base_tags
        return base_tags

    @property
    def get_computed_tags(self):
        """ Returns the computed tag TaggableManager, or creates it if it doesn't exist """
        try:
            computed_tags = self.computed_tags.computed_tags
        except ObjectDoesNotExist:
            computed_tags = ItemComputedTags.objects.create(item=self).computed_tags
        return computed_tags

    def compute_tags(self, recursion=True):
        """ Takes the base tags and computes all parent tags. """
        base_tags = self.get_base_tags
        computed_tags = self.get_computed_tags

        tags_to_search = list(base_tags.all().values_list('pk', flat=True))
        already_searched = list()
        while True:
            tags_to_search = list(set(tags_to_search) - set(already_searched))
            if len(tags_to_search) == 0:
                break
            already_searched += tags_to_search
            tags_to_search = list(Tag.objects.filter(children__child_tag__in=tags_to_search)
                                  .values_list('pk', flat=True))
        already_searched = Tag.objects.filter(pk__in=already_searched)
        computed_tags.set(already_searched, clear=True)

        try:
            tag = Tag.objects.get(name='Item: '+str(self.name))
        except ObjectDoesNotExist:
            tag = Tag.objects.create(name='Item: '+str(self.name))

        try:
            tag_parents = TagParent.objects.get(child_tag=tag)
        except ObjectDoesNotExist:
            tag_parents = TagParent.objects.create(child_tag=tag)

        tag_parents.parent_tag.set(list(base_tags.all())+list(already_searched))
        if recursion:
            tag_parents.compute_descendant_tags()

    def compute_playtime(self):
        """ Function to compute the playtime of the item. Called when saving. """
        if self.average_play_time is None and (self.min_play_time is not None and self.max_play_time is not None):
            # Set average to be equal to average of min and max.
            self.average_play_time = (self.min_play_time + self.max_play_time) // 2

    def save(self, *args, **kwargs):
        """ Computes the playtime and tags upon saving. """
        self.compute_playtime()
        super(Item, self).save(*args, **kwargs)
        self.compute_tags()

    @property
    def url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return reverse('library:detail', args=[self.slug])

    def __str__(self):
        return self.name

    @property
    def availability(self):
        return self.get_availability_info()

    def get_availability_info(self):
        """
        Returns a dict, containing keys:
        'in_clubroom', 'is_available', 'expected_availability_date', 'max_due_date'
        If is_available is True, or if the item is never borrowable,
        then expected_availability_date will be None
        For this, we assume that if you can't borrow an item overnight, then it's not available.
        """
        info = {
            'in_clubroom': True,
            'is_available': True,
            'expected_availability_date': None,
            'max_due_date': None,
        }

        if self.is_borrowable is False:
            info['is_available'] = False
            return info

        today = datetime.date.today()
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
                .exclude(form__form_status__in=[UNAPPROVED, DENIED, COMPLETED]) \
                .filter(date_borrowed__lte=today, date_returned=None) \
                .order_by('-form__due_date')
            if ext_records.exists():
                info['in_clubroom'] = False
                info['is_available'] = False
                info['expected_availability_date'] = ext_records.first().form.due_date
        if info['is_available'] is True:
            # We also check if an external form is lodged for tomorrow
            tomorrow_ext_records = self.ext_borrow_records \
                .exclude(form__form_status__in=[UNAPPROVED, DENIED, COMPLETED]) \
                .filter(form__requested_borrow_date=today+next_day) \
                .order_by('-form__due_date')
            if tomorrow_ext_records.exists():
                info['is_available'] = False
                info['expected_availability_date'] = tomorrow_ext_records.first().form.due_date

        if info['is_available'] is False:
            # We check here to see how the chain of external borrowing forms could affect the availability date
            while True:
                qs = self.ext_borrow_records \
                    .exclude(form__form_status__in=[UNAPPROVED, DENIED, COMPLETED]) \
                    .filter(Q(form__requested_borrow_date=info['expected_availability_date'] + next_day)
                            | Q(form__requested_borrow_date=info['expected_availability_date'])) \
                    .order_by('-form__due_date')
                if qs.exists() is False:
                    break
                info['expected_availability_date'] = qs.first().form.due_date

        if info['is_available'] is True:
            # The item is confirmed available, so calculate the maximum due date for it.
            due_dates = [today+datetime.timedelta(weeks=2)]

            if self.high_demand:
                if today.weekday() in [4, 5, 6]:
                    # High-demand items are borrowable until the next weekday.
                    # So if today is a Friday or a Weekend, it's borrowable until Monday
                    due_dates.append(today+datetime.timedelta(days=7-today.weekday()))
                else:
                    # Else just until tomorrow
                    due_dates.append(today+next_day)

            # Finally, if there's a pending external borrowing form,
            # make sure to have the item returned before then
            qs = self.ext_borrow_records \
                .exclude(form__form_status__in=[UNAPPROVED, DENIED, COMPLETED]) \
                .filter(form__requested_borrow_date__gte=today) \
                .order_by('-form__due_date')

            if qs.exists():
                due_dates.append(qs.first().form.requested_borrow_date+datetime.timedelta(days=-1))

            info['max_due_date'] = min(due_dates)

        return info

    @property
    def is_available(self):
        """
        March 31st 2023: I don't believe this function is used by anything.
        Use get_availability_info above.

        --

        Returns True if the item is both borrowable and available
        Otherwise returns False
        """
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
        if self.ext_borrow_records.filter(form__requested_borrow_date=tomorrow).exists():
            return False
        return True

    @property
    def all_tags(self):
        return self.get_base_tags.all().union(self.get_computed_tags.all())

    @property
    def players_display(self):
        # Returns a string rep of the player count
        if not (self.min_players or self.max_players):
            # No players specified
            return ""
        if self.min_players == self.max_players:
            if self.max_players == 1:
                return "1 player"
            else:
                return "{0} players".format(self.max_players)
        if not self.max_players:
            # There's a min but no max
            return "{0}+ players".format(self.min_players)
        if not self.min_players:
            # There's a max but no min
            return "1 - {0} players".format(self.max_players)
        return "{0} - {1} players".format(self.min_players, self.max_players)

    @property
    def play_time_display(self):
        def convert_minutes_to_hours(mins):
            hours = mins // 60
            plural_hours = 's' if hours != 1 else ''
            minutes = mins % 60
            plural_minutes = 's' if minutes != 1 else ''
            if hours == 0:
                return "{0} min{1}".format(minutes, plural_minutes)
            elif minutes == 0:
                return "{0} hour{1}".format(hours, plural_hours)
            else:
                return "{0} hour{1} {2} min{3}".format(hours, plural_hours, minutes, plural_minutes)
        # Returns a string rep of the play time
        # If there's no average, then return nothing.
        if not self.average_play_time:
            return ""
        else:
            if self.min_play_time is not None and self.max_play_time is not None:
                # All three are set, display all three.
                return "<i>{0}</i> to <i>{1}</i><br />Avg: ~<i>{2}</i>".format(
                    convert_minutes_to_hours(self.min_play_time),
                    convert_minutes_to_hours(self.max_play_time),
                    convert_minutes_to_hours(self.average_play_time)
                )
            else:
                # Simply display the average:
                return "~<i>{0}</i>".format(convert_minutes_to_hours(self.average_play_time))


class ItemBaseTags(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='base_tags')
    base_tags = TaggableManager(blank=True)

    def __str__(self):
        return 'Base tags for '+self.item.name


class ItemComputedTags(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='computed_tags')
    computed_tags = TaggableManager(blank=True)

    def __str__(self):
        return 'Computed tags for '+self.item.name


class BorrowRecord(models.Model):
    # These fields are set upon the item being borrowed
    borrowing_member = models.ForeignKey(
        Member,
        null=True,
        on_delete=models.SET_NULL,
        related_name='borrowed'
    )
    member_address = models.CharField(max_length=200, null=True)
    member_phone_number = models.CharField(max_length=20, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='borrow_records')
    date_borrowed = models.DateField(default=timezone.now)
    auth_gatekeeper_borrow = models.ForeignKey(
        Member,
        null=True,
        on_delete=models.SET_NULL,
        related_name='authorised_borrowing'
    )

    # Due date can be manually set, but is automatically set for two weeks from now
    # (other factors may modify the due date)
    due_date = models.DateField(default=two_weeks_from_now)

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

    def __str__(self):
        if self.verified_returned:
            return '(RETURNED)'+str(self.borrowing_member)+' - '+str(self.item)
        else:
            return str(self.borrowing_member)+' - '+str(self.item)+' (Due '+self.due_date.strftime('%a %b %d')+')'

    def clear_personal_data(self):
        self.borrowing_member = None
        self.member_address = None
        self.member_phone_number = None
        self.auth_gatekeeper_borrow = None
        self.auth_gatekeeper_return = None
        self.save()


class ExternalBorrowingForm(models.Model):
    UNAPPROVED = UNAPPROVED
    DENIED = DENIED
    APPROVED = APPROVED
    COMPLETED = COMPLETED  # For forms that were approved and have been fully completely

    STATUS_CHOICES = [
        (UNAPPROVED, 'Unapproved'),
        (DENIED, 'Denied'),
        (APPROVED, 'Approved'),
        (COMPLETED, 'Completed'),
    ]

    applicant_name = models.CharField(max_length=200)
    applicant_org = models.CharField(max_length=200, blank=True)
    event_details = models.TextField()
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    form_submitted_date = models.DateField(default=datetime.date.today)
    requested_borrow_date = models.DateField()

    form_status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    due_date = models.DateField(blank=True, null=True, default=None)
    librarian_comments = models.TextField(blank=True)


class ExternalBorrowingItemRecord(models.Model):
    form = models.ForeignKey(ExternalBorrowingForm, on_delete=models.CASCADE, related_name='requested_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='ext_borrow_records')

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


class Reservation(models.Model):
    borrower_name = models.CharField(max_length=100)
    contact_info = models.TextField()  # Email, or email + phone
    reserved_items = models.ManyToManyField(Item, related_name="reservations")  # Items to be reserved.
    date_from = models.DateField()  # Date that the items shall be collected
    date_to = models.DateField()  # Date that the items should be returned on.

    active = models.BooleanField(default=False)  # Whether the reservation is "active".
    # Defaults to False. Librarian approving a form sets this to True.
    # Reservation is ignored by all logic if active is False or date_from is in the past.

    item_borrow_records = models.ManyToManyField(BorrowRecord, blank=True)  # Links the reservation to the BorrowRecords for it.


class InternalReservationRequest(models.Model):
    """
    This model handles reservations for Unigames members.
    Non-members should be handled using ExternalReservationRequest.
    """
    borrower = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, default=None)
    from_date = models.DateField()
    to_date = models.DateField()
    details = models.TextField()

    submitted = models.DateTimeField(auto_now_add=True)

    approval_statys = models.CharField



