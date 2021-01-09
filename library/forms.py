from django import forms
from dal import autocomplete
from .models import Item
from crispy_forms.helper import FormHelper


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


class ItemSelectForm(forms.Form):
    # Used to select items for borrowing purposes
    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url='library:item-autocomplete')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

