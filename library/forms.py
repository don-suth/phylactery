from django import forms
from dal import autocomplete
from .models import StrTag, StrTagValue, StrTagThrough


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

