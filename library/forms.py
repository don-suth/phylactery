from django import forms
from dal import autocomplete
from .models import Item, ItemBaseTags, ItemComputedTags
from crispy_forms.helper import FormHelper


class ItemTaggitForm(autocomplete.FutureModelForm):
    class Meta:
        model = Item
        fields = (
            'name', 'slug', 'description',
            'condition', 'type', 'image',
            'is_borrowable', 'high_demand', 'notes'
        )


class BaseTagForm(autocomplete.FutureModelForm):
    class Meta:
        model = ItemBaseTags
        fields = ('base_tags',)
        widgets = {
            'base_tags': autocomplete.TaggitSelect2('library:select2_taggit', attrs={'style': 'width: 100%;'})
        }


class ComputedTagForm(autocomplete.FutureModelForm):
    class Meta:
        model = ItemComputedTags
        fields = ('computed_tags',)
        widgets = {
            'computed_tags': autocomplete.TaggitSelect2('library:select2_taggit', attrs={'disabled': True})
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

