from django.test import TestCase
from .models import Item, BorrowRecord, ExternalBorrowingForm
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


def create_member(first_name='Donald', last_name='Sutherland', email_address='donald@sutherland.id.au'):
    return Member.objects.create(
        first_name=first_name,
        last_name=last_name,
        email_address=email_address
    )


def create_item(name='D&D 5e PHB', type='BK'):
    return Item.objects.create(
        name=name,
        type=type
    )


def create_borrow_record(
        borrowing_member, item, auth_gatekeeper_borrow, member_address='123 Blah Street',
        member_phone_number='0123455678', date_borrowed=-1, due_date=1, date_returned=None,
        auth_gatekeeper_return=None, verified_returned=False):

    today = timezone.now()
    if type(date_borrowed) is int:
        date_borrowed = today + datetime.timedelta(days=date_borrowed)
    if type(date_returned) is int:
        date_returned = today + datetime.timedelta(days=date_returned)
    if type(due_date) is int:
        due_date = today + datetime.timedelta(days=due_date)

    return BorrowRecord.objects.create(
        borrowing_member=borrowing_member,
        item=item,
        date_borrowed=date_borrowed,
        auth_gatekeeper_borrow=auth_gatekeeper_borrow,
        auth_gatekeeper_return=auth_gatekeeper_return,
        due_date=due_date,
        member_address=member_address,
        member_phone_number=member_phone_number,
        date_returned=date_returned,
        verified_returned=verified_returned
    )


def create_ext_borrow_record(
        requested_items, form=None, applicant_name='Smonald Dunderland', applicant_org='Punygames',
        event_details='Totally not going to damage the books', contact_phone='0123456789',
        contact_email='fake@email.com.au', requested_borrow_date=1, due_date=2, date_borrowed=1,
        date_returned=2, auth_gatekeeper_borrow=None, borrower_name='Smonald Dunderland',
        auth_gatekeeper_return=None, verified_returned=False, form_status='U'):

    today = timezone.now()
    if type(requested_borrow_date) is int:
        requested_borrow_date = today + datetime.timedelta(days=requested_borrow_date)
    if type(date_borrowed) is int:
        date_borrowed = today + datetime.timedelta(days=date_borrowed)
    if type(date_returned) is int:
        date_returned = today + datetime.timedelta(days=date_returned)
    if type(due_date) is int:
        due_date = today + datetime.timedelta(days=due_date)

    if auth_gatekeeper_return is None and auth_gatekeeper_borrow is None:
        auth_gatekeeper_borrow = auth_gatekeeper_return = create_member()
    elif auth_gatekeeper_borrow is None:
        auth_gatekeeper_borrow = create_member()
    elif auth_gatekeeper_return is None:
        auth_gatekeeper_return = create_member()

    if form is None:
        form = ExternalBorrowingForm.objects.create(
            applicant_name=applicant_name,
            applicant_org=applicant_org,
            event_details=event_details,
            contact_phone=contact_phone,
            contact_email=contact_email,
            due_date=due_date,
            form_status=form_status,
            requested_borrow_date=requested_borrow_date,
        )
    for item in requested_items:
        form.requested_items.create(
            item=item,
            auth_gatekeeper_return=auth_gatekeeper_return,
            auth_gatekeeper_borrow=auth_gatekeeper_borrow,
            date_borrowed=date_borrowed,
            date_returned=date_returned,
            borrower_name=borrower_name,
        )
    return form



class LibraryModelTests(TestCase):

    def test_availability_info(self):
        member1 = create_member()
        dnd = create_item()
        borrow_record = create_borrow_record(member1, dnd, member1,
                                             date_borrowed=datetime.date(2020, 9, 30),
                                             due_date=datetime.date(2020, 10, 3))

        with freeze_time('1st October 2020') as frozen_time:
            info = dnd.get_availability_info()
            self.assertEqual(info['in_clubroom'], False)
            self.assertEqual(info['is_available'], False)
            self.assertEqual(info['expected_availability_date'], datetime.date(2020, 10, 3))

        with freeze_time('3rd October 2020') as frozen_time:
            info = dnd.get_availability_info()
            self.assertEqual(info['in_clubroom'], False)
            self.assertEqual(info['is_available'], False)        # On October 3rd, he asked me what the date was
            self.assertEqual(info['expected_availability_date'], datetime.date(2020, 10, 3))  # It's October 3rd

            borrow_record.date_returned = datetime.date(2020, 10, 3)
            borrow_record.save()

            info = dnd.get_availability_info()
            self.assertEqual(info['in_clubroom'], True)
            self.assertEqual(info['is_available'], True)
            self.assertEqual(info['expected_availability_date'], None)

            ext_borrow_record = create_ext_borrow_record(
                [dnd], auth_gatekeeper_borrow=member1, auth_gatekeeper_return=member1,
                requested_borrow_date=datetime.date(2020, 10, 4), due_date=datetime.date(2020, 10, 5),
                form_status='A'
            )

            info = dnd.get_availability_info()
            self.assertEqual(info['in_clubroom'], True)
            self.assertEqual(info['is_available'], False)
            self.assertEqual(info['expected_availability_date'], datetime.date(2020, 10, 5))

            ext_borrow_record_2 = create_ext_borrow_record(
                [dnd], auth_gatekeeper_borrow=member1, auth_gatekeeper_return=member1,
                requested_borrow_date=datetime.date(2020, 10, 6), due_date=datetime.date(2020, 10, 8),
                form_status='A'
            )

            info = dnd.get_availability_info()
            self.assertEqual(info['in_clubroom'], True)
            self.assertEqual(info['is_available'], False)
            self.assertEqual(info['expected_availability_date'], datetime.date(2020, 10, 8))
