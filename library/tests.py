from django.test import TestCase
from .models import Item, ItemTypes, BorrowRecord, ExternalBorrowingRecord
from members.models import Member
from django.utils import timezone
import datetime
from freezegun import freeze_time


'''
Tests to make:
    - item tagging
    - searching items by tag (when implemented)
    - searching in general (when implemented)
    - hierarchical tags on item save (when implemented)
    - hierarchical tags on force refresh (when implemented)
    - borrow item, check if available
    - borrow item, check availability date
    - return item, check if available
    - borrow item, with external form, check availability date
'''


class LibraryModelTests(TestCase):
    def setUp(self):
        ItemTypes.objects.create(type_name="Book")
        Item.objects.create(
            item_name="Dungeons & Dragons Players Handbook 5th Edition",
            item_type=ItemTypes.objects.get(type_name='Book'),
        )
        Member.objects.create(
            first_name='Donald',
            last_name='Sutherland',
            email_address='donald@sutherland.id.au',
        )

    @freeze_time("9th January 2021")
    def test_availability_info(self):
        today = timezone.now()
        self.assetEqual(today, datetime.date(2021, 1, 9))

        currently_borrowed = BorrowRecord.objects.create(
            borrowing_member=Member.objects.get(first_name='Donald'),
            member_address='123 Fake Avenue, 9999',
            member_phone_number='0123456789',
            item=Item.objects.get(pk=1),
            date_borrowed=today - datetime.timedelta(days=1),
            auth_gatekeeper=Member.objects.get(first_name='Donald'),
            due_date=today + datetime.timedelta(days=1)
        )