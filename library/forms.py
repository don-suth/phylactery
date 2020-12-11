from django import forms
from dal import autocomplete
from .models import Item


class ItemTaggitForm(autocomplete.FutureModelForm):
    class Meta:
        model = Item
        fields = (
            'name', 'slug', 'description',
            'condition', 'notes', 'type',
            'image', 'tags'
        )
        widgets = {
            'tags': autocomplete.TaggitSelect2('library:select2_taggit')
        }
