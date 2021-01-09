from django.test import TestCase
from .models import Item, ItemTypes


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
        book_type = ItemTypes.objects.create(type_name="Book")
        Item.objects.create(
            item_name="Dungeons & Dragons Players Handbook 5th Edition",
            item_type=book_type,
        )
