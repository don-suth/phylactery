from django.test import TestCase
from .models import Item, ItemTypes


class LibraryModelTests(TestCase):
    def setUp(self):
        ItemTypes.objects.create(type_name="Book")
        ItemTypes.objects.create(type_name="Board Game")
        Item.objects.create(
            item_name="Dungeons & Dragons Players Handbook 5th Edition",
            item_type=ItemTypes.objects.get(type_name="Book"),
        )
        Item.objects.create(
            item_name="Dungeons & Dragons Monster Manual 5th Edition",
            item_type=ItemTypes.objects.get(type_name="Book"),
        )
        Item.objects.create(
            item_name="Galaxy Truckers",
            item_type=ItemTypes.objects.get(type_name="Board Game"),
        )

    def test_fetch_all_books(self):
        qs = Item.objects.filter(item_type__type_name="Book")
        self.assertQuerysetEqual(qs,
                                 ['<Item: Dungeons & Dragons Players Handbook 5th Edition>',
                                  '<Item: Dungeons & Dragons Monster Manual 5th Edition>'],
                                 ordered=False)

    def test_fetch_all_board_games(self):
        qs = Item.objects.filter(item_type__type_name="Board Game")
        self.assertQuerysetEqual(qs,
                                 ['<Item: Galaxy Truckers>'],
                                 ordered=False)
