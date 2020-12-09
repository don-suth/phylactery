from django import forms
from dal import autocomplete
from .models import Item


class ItemTaggitForm(autocomplete.FutureModelForm):
    class Meta:
        model = Item
        fields = (
            'item_name', 'item_slug', 'item_description',
            'item_condition', 'item_notes', 'item_type',
            'item_image', 'tags'
        )
        widgets = {
            'tags': autocomplete.TaggitSelect2('library:select2_taggit')
        }
