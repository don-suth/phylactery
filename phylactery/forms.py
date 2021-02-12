from members.models import Member, UnigamesUser, Rank, RankAssignments, MemberFlag
from django import forms
from django.core.exceptions import ImproperlyConfigured
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, PrependedText
from django.utils.text import slugify
from django.contrib.admin import widgets


class ControlPanelForm(forms.Form):
    # Base class for control panel forms.
    # Forms are rendered as bootstrap cards, with a button that opens up a modal to confirm the form.
    # Provides a mandatory checkbox to confirm the action as well
    # Control panel forms should:
    # - have a name and description (will be rendered to the user)
    # - have a submit function that does their thing
    # - define self.helper.form_action - the reversible url to submit the form to
    # - define self.helper.layout - the layout of the form inside the bootstrap modal

    confirmation = forms.BooleanField(required=True, label='I confirm that I wish to perform this action.')

    form_name = ''
    form_description = ''
    form_media = False
    form_tag = True
    form_method = 'post'
    form_action = None
    layout = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slug_name = slugify(self.form_name)

        self.helper = FormHelper()
        self.helper.include_media = self.form_media
        self.helper.form_tag = self.form_tag
        self.helper.form_method = self.form_method
        if self.form_action is not None:
            self.helper.form_action = self.form_action
        else:
            raise ImproperlyConfigured('You must define a form action')
        if self.layout is not None:
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
                        css_class='card-body'
                    ),
                    css_class='card text-center'
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
                                HTML('<p>{0}</p><hr>'.format(self.form_description)),
                                self.layout,
                                'confirmation',
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


class PurgeAllGatekeepers(ControlPanelForm):
    # When submitted, removes the gatekeeper rank from all non-committee members
    form_action = 'phylactery:control-1'
    form_name = 'Purge all Gatekeepers'
    form_description = 'Remove the gatekeeper status of all non-committee gatekeepers.'

    layout = Layout()

    def submit(self):
        # Do the thing!
        pass


class ExpireMemberships(ControlPanelForm):
    # When submitted, expires any memberships of members before the given date.
    # Default is 1st Jan this year.
    form_action = 'phylactery:control-2'
    form_name = "Invalidate Memberships"
    form_description = 'Marks any memberships gotten before the given date as expired. '\
                       'Defaults to 1st of January this year.'
    form_media = True

    cut_off_date = forms.DateField(
        label='Invalidate memberships purchased before:',
        widget=widgets.AdminDateWidget,
    )

    layout = Layout(
        'cut_off_date'
    )

    def submit(self):
        # Do the thing!
        pass

    class Media:
        css = {
            'all': ('admin/css/widgets.css', 'phylactery/responsive_calendar.css')
        }
        js = ('/jsi18n/', 'admin/js/core.js', 'admin/js/calendar.js', 'admin/js/admin/DateTimeShortcuts.js')
