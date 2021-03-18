from django import forms
from dal import autocomplete
from .models import Item, ItemBaseTags, ItemComputedTags, \
    BorrowRecord, ExternalBorrowingForm
from members.models import Member
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, HTML, Submit
from django.conf import settings
from django.contrib.admin import widgets
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import RegexValidator
from django.utils import timezone
import datetime


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
    item = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        required=True,
        queryset=Item.objects.all(),
    )
    due_date = forms.DateField(required=True, widget=widgets.AdminDateWidget)

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data['item']
        due_date = cleaned_data['due_date']
        item_info = item.get_availability_info()
        if not item_info['is_available']:
            raise ValidationError("{0} is not available to borrow at the moment.".format(item.name))
        if due_date > item_info['max_due_date']:
            self.add_error(
                'due_date',
                "Due date can't go past the max due date for this item ({0})".format(str(item_info['max_due_date']))
            )
        if due_date < datetime.date.today():
            self.add_error(
                'due_date',
                "Due date can't be in the past."
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('''
            {% load library_extras %}
            <tr{% if forloop.counter0|warn_different_due:diff %} class="table-warning"{% endif %}>
                <td class="image-col"><img class="list-card-image-sm" src="{{ item_form.item|get_item_attr:'image.url' }}"></td>
                <td>{{ item_form.item|get_item_attr:'name' }}</td>
                <td class="date-col">
            '''),
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
                    <p>Choose the items that the member is borrowing. Member details will be filled out later.</p>
                """),
                'items',
                Submit('submit', 'Submit', css_class='btn-primary'),
            ),
        )


class MemberBorrowDetailsForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=CrispyModelSelect2(url='members:autocomplete', attrs={'style': 'width:100%'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True
    )
    phone_number = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={'type': 'tel'}),
        validators=[RegexValidator(
            regex="^[0-9]+$",
            message="Please enter your phone number without any special characters."
        )]
    )

    def clean_member(self):
        member = self.cleaned_data['member']
        if member.has_rank('EXCLUDED'):
            raise ValidationError('This member cannot borrow items.')
        if not member.is_member:
            raise ValidationError("This member's membership is not valid.")
        return member

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Enter the member details below',
                Div(
                    Div(
                        'member',
                        css_class="col-md"
                    ),
                    Div(
                        'phone_number',
                        css_class="col-sm"
                    ),
                    Div(
                        'address',
                        css_class="col-sm"
                    ),
                    css_class="form-row"
                ),
            )
        )


class VerifyReturnForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for record in BorrowRecord.objects.exclude(date_returned=None).exclude(verified_returned=True):
            field_name = 'return_' + str(record.pk)
            self.fields[field_name] = forms.BooleanField(required=False)


class ReturnItemsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.member_pk = kwargs.pop('member_pk', None)
        super().__init__(*args, **kwargs)
        if self.member_pk:
            self.qs = BorrowRecord.objects.filter(date_returned=None, borrowing_member=self.member_pk)
            for record in self.qs:
                field_name = 'return_' + str(record.pk)
                self.fields[field_name] = forms.BooleanField(required=False)
        else:
            raise ImproperlyConfigured('No Member pk was given')


class ExternalBorrowingRequestForm(forms.Form):
    applicant_name = forms.CharField(
        required=True,
        label='Your name',
    )
    applicant_org = forms.CharField(
        required=False,
        label='Your organisation name (optional)',
    )
    event_details = forms.CharField(
        required=True,
        label='Enter additional details about your event and organisation (if applicable) here.',
        widget=forms.Textarea(attrs={'rows': '5'}),
    )
    contact_phone = forms.CharField(
        required=True,
        label='Contact Phone Number',
        widget=forms.TextInput(attrs={'type': 'tel'})
    )
    contact_email = forms.EmailField(
        required=True,
        label='Contact Email',
    )
    requested_borrow_date = forms.DateField(
        required=True,
        widget=widgets.AdminDateWidget,
    )
    requested_items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        widget=CrispyModelSelect2Multiple(url='library:item-autocomplete', attrs={'style': 'width: 100%;'})
    )

    confirmed = forms.BooleanField(
        required=True,
        label='I agree to the above'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.include_media = False
        self.helper.layout = Layout(
            Fieldset(
                'External Borrowing Request Form',
                HTML("""
                    <p>Unigames allows other clubs, organisations and people to borrow items for their events.
                    This is a form to request items to borrow for such an event.</p>
                    <p>To guarantee that we can provide all items that your request, we ask that this form 
                    be submitted with a minimum of two weeks notice, with ideally three weeks notice.</p>
                    <p>Make sure the contact information you enter is correct, as the Librarian will
                    contact you to discuss your request.</p>
                """),
                Div(
                    Div(
                        'applicant_name',
                        css_class='col-md'
                    ),
                    Div(
                        'applicant_org',
                        css_class='col-md'
                    ),
                    css_class='form-row'
                ),
                'event_details',
                Div(
                    Div(
                        'contact_phone',
                        css_class='col-md'
                    ),
                    Div(
                        'contact_email',
                        css_class='col-md'
                    ),
                    Div(
                        'requested_borrow_date',
                        css_class='col-md',
                    ),
                    css_class='form-row'
                ),
                'requested_items',
                HTML('''
                <p>By checking this box, you understand and agree to the following:
                    <ul>
                        <li>That a Unigames representative will contact you to discuss details about this 
                            borrowing request with you.</li>
                        <li>Unigames has the full right to approve or deny this request for any reason.</li>
                        <li>It may not be possible to get you all the games that you request.</li>
                        <li>You/Your organisation will be responsible for all costs in the event that the item is 
                            damaged or not returned.</li>
                    </ul>
                </p>
                '''),
                'confirmed',
                Submit('submit', 'Submit', css_class='btn-primary'),
            ),
        )

    def submit(self):
        new_form = ExternalBorrowingForm.objects.create(
            applicant_name=self.cleaned_data['applicant_name'],
            applicant_org=self.cleaned_data['applicant_org'],
            event_details=self.cleaned_data['event_details'],
            contact_phone=self.cleaned_data['contact_phone'],
            contact_email=self.cleaned_data['contact_email'],
            requested_borrow_date=self.cleaned_data['requested_borrow_date'],
            form_status=ExternalBorrowingForm.UNAPPROVED,
        )
        for item in self.cleaned_data['requested_items']:
            new_form.requested_items.create(
                item=item
            )
