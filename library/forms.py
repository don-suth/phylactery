from django import forms
from dal import autocomplete
from .models import StrTag, StrTagValue, StrTagThrough, Item
from taggit.forms import TagField


class StrTagThroughForm(forms.ModelForm):
    tag = forms.ModelChoiceField(
        queryset=StrTag.objects.all()
    )
    value = forms.ModelChoiceField(
        queryset=StrTagValue.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='library:strtagvalue-autocomplete',
            forward=['tag']
        )
    )

    class Meta:
        model = StrTagThrough
        fields = ('__all__')


class ItemTaggitForm(autocomplete.FutureModelForm):
    class Meta:
        model = Item
        fields = ('item_name', 'item_slug', 'item_description', 'item_condition', 'item_notes', 'item_type', 'tags')
        widgets = {
            'tags': autocomplete.TaggitSelect2('library:select2_taggit')
        }
