from members.models import Member, UnigamesUser, Rank, RankAssignments, MemberFlag
from django import forms
from django.core.exceptions import ImproperlyConfigured
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, PrependedText
from django.utils.text import slugify
from django.contrib.admin import widgets
from django.shortcuts import reverse
from django.forms import ValidationError
import datetime


class ControlPanelForm(forms.Form):
    # Base class for control panel forms.
    # Forms are rendered as bootstrap cards, with a button that opens up a modal to confirm the form.
    # Provides a mandatory checkbox to confirm the action as well
    # Control panel forms should:
    # - have a name and description (will be rendered to the user)
    # - have an optional long description that will show when the panel is opened
    # - have a submit function that does their thing
    # - define self.helper.form_action - the reversible url to submit the form to
    # - define self.helper.layout - the layout of the form inside the bootstrap modal
    # - define form_permissions, a whitelist of Ranks that can operate this form

    form_name = ''
    form_description = ''
    form_long_description = ''
    form_permissions = []
    form_media = False
    form_tag = True
    form_method = 'post'
    form_action = 'control-panel'
    layout = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slug_name = slugify(self.form_name)

        self.fields['form_slug_name'] = forms.CharField(widget=forms.HiddenInput(), initial=self.slug_name)
        confirmation_name = self.slug_name+'_confirmation'
        self.fields[confirmation_name] = forms.BooleanField(required=True, label='I confirm that I wish to perform this action.')

        self.helper = FormHelper()
        self.helper.include_media = self.form_media
        self.helper.form_tag = self.form_tag
        self.helper.form_method = self.form_method
        if self.form_action is not None:
            self.helper.form_action = reverse(self.form_action)
        else:
            raise ImproperlyConfigured('You must define a form action')
        if self.layout is not None:
            self.is_valid()
            if self.errors:
                card_border = 'border-danger'
                card_text = 'text-danger'
            else:
                card_border = ''
                card_text = ''
            self.helper.layout = Layout(
                Div(
                    Div(
                        HTML('''<h5 class="card-title">{0}</h5>
                        <p class="card-text">{1}</p>'''
                             .format(self.form_name, self.form_description)),
                        StrictButton(
                            'Open Panel',
                            css_class='btn btn-primary',
                            data_toggle='modal',
                            data_target='#{0}-modal'.format(self.slug_name)
                        ),
                        css_class='card-body '+card_text
                    ),
                    css_class='card text-center '+card_border
                ),
                Div(
                    Div(
                        Div(
                            Div(
                                HTML('''<h5 class="modal-title" id="{0}-modal-title">{1}</h5>'''
                                     .format(self.slug_name, self.form_name)),
                                StrictButton('&times;', css_class='btn-close', data_dismiss='modal',
                                             aria_label='Close'),
                                css_class="modal-header"
                            ),
                            Div(
                                HTML('<p>{0}</p><p>{1}</p><hr>'.format(
                                    self.form_description,
                                    self.form_long_description)
                                ),
                                self.layout,
                                confirmation_name,
                                'form_slug_name',
                                css_class="modal-body"
                            ),
                            Div(
                                StrictButton('Close', css_class='btn-secondary', data_dismiss='modal'),
                                Submit('submit', 'Submit and Perform action', css_class='btn-primary'),
                                css_class="modal-footer"
                            ),
                            css_class="modal-content"
                        ),
                        css_class="modal-dialog"
                    ),
                    css_class="modal fade",
                    css_id="{0}-modal".format(self.slug_name),
                    aria_labelledby="{0}-modal-title".format(self.slug_name),
                    tabindex="-1",
                    aria_hidden="true",
                )
            )
        else:
            raise ImproperlyConfigured('You must define a form layout')

    def submit(self, request):
        pass


class PurgeAllGatekeepers(ControlPanelForm):
    # When submitted, removes the gatekeeper rank from all non-committee members
    form_name = 'Purge all Gatekeepers / Webkeepers'
    form_description = 'Remove the gatekeeper or webkeeper status of all non-committee members.'
    form_long_description = ''
    form_permissions = ['President', 'Vice-President', 'Secretary']

    layout = Layout()

    def submit(self):
        # Do the thing!
        pass


class ExpireMemberships(ControlPanelForm):
    # When submitted, expires any memberships of members before the given date.
    # Default is 1st Jan this year.
    form_name = "Invalidate Memberships"
    form_description = 'Marks any memberships gotten before the given date as expired. '\
                       'Defaults to 1st of January this year.'
    form_media = True
    form_permissions = ['President', 'Vice-President', 'Secretary']

    cut_off_date = forms.DateField(
        label='Invalidate memberships purchased before:',
        widget=widgets.AdminDateWidget,
        initial=datetime.date.today().replace(day=1, month=1)
    )

    layout = Layout(
        'cut_off_date'
    )

    def clean_cut_off_date(self):
        today = datetime.date.today()
        date = self.cleaned_data['cut_off_date']
        if date > today:
            raise ValidationError('Date cannot be in the future.', code='future')

    def submit(self):
        # Do the thing!
        pass

    class Media:
        css = {
            'all': ('admin/css/widgets.css', 'phylactery/responsive_calendar.css')
        }
        js = ('/jsi18n/', 'admin/js/core.js', 'admin/js/calendar.js', 'admin/js/admin/DateTimeShortcuts.js')


class MakeGatekeepers(ControlPanelForm):
    form_name = 'Promote Members to Gatekeepers'
    form_description = 'Promotes the selected members to gatekeepers.'
    layout = Layout()
    form_permissions = ['President', 'Vice-President', 'Secretary']


class TransferCommittee(ControlPanelForm):
    form_name = 'Transfer Committee Roles'
    form_description = 'Transfers any/all roles of committee to others'
    layout = Layout()
    form_permissions = ['President', 'Vice-President']

