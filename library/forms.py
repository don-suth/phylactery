from django import forms
from dal import autocomplete
from .models import Item, ItemBaseTags, ItemComputedTags
from members.models import Member
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, HTML, Submit
from django.conf import settings
from django.contrib.admin import widgets



class CrispyModelSelect2(autocomplete.ModelSelect2):
    @property
    def media(self):
        """Return JS/CSS resources for the widget."""
        extra = '' if settings.DEBUG else '.min'
        i18n_name = self._get_language_code()
        i18n_file = (
            'vendor/select2/dist/js/i18n/%s.js' % i18n_name,
        ) if i18n_name else ()

        return forms.Media(
            js=(
                   'autocomplete_light/jquery.init.js',
                   'phylactery/select2.full%s.js' % extra,
               ) + i18n_file + (
                   'autocomplete_light/autocomplete.init.js',
                   'autocomplete_light/forward.js',
                   'autocomplete_light/select2.js',
                   'autocomplete_light/jquery.post-setup.js',
               ),
            css={
                'screen': (
                    'phylactery/select2%s.css' % extra,
                    'admin/css/autocomplete.css',
                    'autocomplete_light/select2.css',
                ),
            },
        )


class CrispyModelSelect2Multiple(autocomplete.ModelSelect2Multiple):
    @property
    def media(self):
        """Return JS/CSS resources for the widget."""
        extra = '' if settings.DEBUG else '.min'
        i18n_name = self._get_language_code()
        i18n_file = (
            'vendor/select2/dist/js/i18n/%s.js' % i18n_name,
        ) if i18n_name else ()

        return forms.Media(
            js=(
                   'autocomplete_light/jquery.init.js',
                   'phylactery/select2.full%s.js' % extra,
               ) + i18n_file + (
                   'autocomplete_light/autocomplete.init.js',
                   'autocomplete_light/forward.js',
                   'autocomplete_light/select2.js',
                   'autocomplete_light/jquery.post-setup.js',
               ),
            css={
                'screen': (
                    'phylactery/select2%s.css' % extra,
                    'admin/css/autocomplete.css',
                    'autocomplete_light/select2.css',
                ),
            },
        )


class ItemDueDateForm(forms.Form):
    item = forms.ModelChoiceField(widget=forms.HiddenInput, required=True, queryset=Item.objects.all())
    due_date = forms.DateField(required=True, widget=widgets.AdminDateWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('''
            {% load library_extras %}
            <tr>
                <td><img class="list-card-image" src="{{ form.item|get_attr:"image.url" }}"></td>"
                <td>{{ form.item|get_attr:"name" }}</td>
                <td>'''),
            'item',
            'due_date',
            HTML('</td></tr>')
        )
        self.helper.include_media = False
        self.helper.form_tag = False


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
    member = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=CrispyModelSelect2(url='members:autocomplete', attrs={'style': 'width:100%'})
    )
    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        widget=CrispyModelSelect2Multiple(url='library:item-autocomplete', attrs={'style': 'width: 100%;'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Borrow Items',
                HTML("""
                    <p>Choose the member that's borrowing items, and the items to borrow below.</p>
                """),
                'member',
                'items',
                Submit('submit', 'Submit', css_class='btn-primary'),
            ),
        )
