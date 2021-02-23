from members.models import Member, UnigamesUser, Rank, RankAssignments, MemberFlag
from library.forms import CrispyModelSelect2, CrispyModelSelect2Multiple
from django import forms
from django.core.exceptions import ImproperlyConfigured
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, PrependedText
from django.utils.text import slugify
from django.contrib.admin import widgets
from django.shortcuts import reverse
from django.forms import ValidationError
from django.contrib import messages
from django.db.models import Q
import datetime
import warnings



class ControlPanelForm(forms.Form):
    # Base class for control panel forms.
    # Forms are rendered as bootstrap cards, with a button that opens up a modal to confirm the form.
    # Provides a mandatory checkbox to confirm the action as well
    # Control panel forms should:
    # - have a name and description (will be rendered to the user)
    # - have an optional long description that will show when the panel is opened
    # - have a submit function that does their thing
    # - define a get_layout function that returns the desired layout
    # - define form_permissions, a whitelist of Ranks that can operate this form

    form_name = ''
    form_description = ''
    form_long_description = ''
    form_permissions = []
    form_media = False
    form_tag = True
    form_method = 'post'
    form_action = 'control-panel'

    def get_layout(self):
        return Layout()

    def __init__(self, *args, **kwargs):
        if kwargs.get('skip_init', None) is True:
            pass
        else:
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
                            self.get_layout(),
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

    def submit(self, request):
        pass


class PurgeAllGatekeepers(ControlPanelForm):
    # When submitted, removes the gatekeeper rank from all non-committee members
    form_name = 'Purge all Gatekeepers / Webkeepers'
    form_description = 'Remove the gatekeeper or webkeeper status of all non-committee members.'
    form_long_description = ''
    form_permissions = ['President', 'Vice-President', 'Secretary']

    CHOICES = [
        ('gatekeeper', 'Gatekeepers'),
        ('webkeeper', 'Webkeepers'),
        ('gatekeeper_webkeeper', 'Gatekeepers and Webkeepers')
    ]

    purge_choice = forms.ChoiceField(choices=CHOICES, label='Purge the status of:', widget=forms.RadioSelect())

    def get_layout(self):
        return Layout(
            'purge_choice'
        )

    def submit(self, request):
        def expire_active_ranks(rank_name):
            today = datetime.date.today()
            committee = Member.objects.filter(
                (Q(ranks__expired_date__gt=today) | Q(ranks__expired_date=None)), ranks__rank__rank_name='COMMITTEE'
            )
            active_ranks = RankAssignments.objects \
                .exclude(expired_date__lte=today) \
                .exclude(member__in=committee) \
                .filter(rank__rank_name=rank_name)
            for rank in active_ranks:
                rank.expired_date = today
                # We save individually rather than doing a mass update so that the Ranks save() method is called
                rank.save()
            return len(active_ranks)
        if self.is_valid():
            choice = self.cleaned_data['purge_choice']

            if choice == 'gatekeeper':
                # Kill all gatekeepers
                num_removed = expire_active_ranks('GATEKEEPER')
                if num_removed > 0:
                    messages.success(request, 'Successfully removed gatekeeper status from {0} non-committee member{1}.'
                                     .format(num_removed, 's' if num_removed != 1 else ''))
                else:
                    messages.warning(request, 'No non-committee gatekeepers to remove.')
            elif choice == 'webkeeper':
                # Kill all webkeepers
                num_removed = expire_active_ranks('WEBKEEPER')
                if num_removed > 0:
                    messages.success(request, 'Successfully removed webkeeper status from {0} non-committee member{1}.'
                                     .format(num_removed, 's' if num_removed != 1 else ''))
                else:
                    messages.warning(request, 'No non-committee webkeepers to remove.')
            elif choice == 'gatekeeper_webkeeper':
                # Kill both
                num_gate_removed = expire_active_ranks('GATEKEEPER')
                num_web_removed = expire_active_ranks('WEBKEEPER')
                if num_gate_removed > 0:
                    messages.success(request, 'Successfully removed gatekeeper status from {0} non-committee member{1}.'
                                     .format(num_gate_removed, 's' if num_gate_removed != 1 else ''))
                else:
                    messages.warning(request, 'No non-committee gatekeepers to remove.')
                if num_web_removed > 0:
                    messages.success(request, 'Successfully removed webkeeper status from {0} non-committee member{1}.'
                                     .format(num_web_removed, 's' if num_web_removed != 1 else ''))
                else:
                    messages.warning(request, 'No non-committee webkeepers to remove.')


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

    def get_layout(self):
        return Layout(
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
    form_media = True

    form_permissions = ['President', 'Vice-President', 'Secretary']

    members_to_add = forms.ModelMultipleChoiceField(
        queryset=Member.objects.all(),
        widget=CrispyModelSelect2Multiple(url='members:autocomplete', attrs={'style': 'width:100%'})
    )

    def get_layout(self):
        return Layout(
            'members_to_add'
        )


class TransferCommittee(ControlPanelForm):
    form_name = 'Transfer Committee Roles'
    form_description = 'Transfers any/all roles of committee to others'
    form_permissions = ['President', 'Vice-President']

    full_committee_change = forms.BooleanField(
        required=False,
        label='Is this Committee change the result of a full committee re-election at an AGM?',
        initial=True
    )

    include_ipp = forms.BooleanField(
        required=False,
        label='Add the immediate past president (IPP) to the new committee?'
    )

    layout = Layout(
    )

    NON_OCM_POSITIONS = [
        'President',
        'Vice-President',
        'Treasurer',
        'Secretary',
        'Librarian',
        'Fresher-Rep',
    ]

    NUMBER_OF_OCMS = 4

    def get_current_committee(self):
        # Find all current committee members
        # Returns a dictionary, keyed with committee rank and a list of members with that rank.
        # There should only be one committee member of each rank, plus some OCMs
        committee = {}
        today = datetime.date.today()
        for position in self.NON_OCM_POSITIONS + ['OCM']:
            # Find the member with the most recent non-expired rank
            committee[position] = Member.objects.filter(
                Q(ranks__expired_date__gt=today) | Q(ranks__expired_date=None),
                ranks__rank__rank_name=position.upper()
            )
        for position in committee:
            if position == 'OCM' and len(committee[position]) != self.NUMBER_OF_OCMS:
                warnings.warn('Committee Error - Number of current OCMs ({0}) is not correct. (Should be {1}.)'
                              .format(len(committee['OCM']), self.NUMBER_OF_OCMS))
            elif len(committee[position]) != 1:
                warnings.warn('Committee Error - Number of members with rank {0} ({1}) is not correct. (Should be 1.)'
                              .format(position, len(committee[position])))
        return committee

    def get_layout(self):
        layout = Layout()
        current_committee = self.get_current_committee()
        layout.append(HTML('<p>Current Committee:</p><ul>'))
        for position in self.NON_OCM_POSITIONS + ['OCM']:
            layout.append(HTML('<li>' + position + ':<ul>'))
            if len(current_committee[position]) == 0:
                layout.append(HTML('<li>None</li>'))
            else:
                for member in current_committee[position]:
                    layout.append(HTML('<li>' + str(member) + '</li>'))
            layout.append(HTML('</ul>'))
        layout.append(HTML('</ul>'))
        layout.append('full_committee_change')
        for position in self.NON_OCM_POSITIONS:
            slug_name = slugify(position)
            layout.append(slug_name)
        for i in range(self.NUMBER_OF_OCMS):
            name = 'OCM #{0}'.format(i + 1)
            slug_name = slugify(name)
            layout.append(slug_name)
        layout.append('include_ipp')

        return layout

    def __init__(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        # Add the fields, generate the layout
        for position in self.NON_OCM_POSITIONS:
            slug_name = slugify(position)
            self.fields[slug_name] = forms.ModelChoiceField(
                queryset=Member.objects.all(),
                widget=CrispyModelSelect2(
                    url='members:autocomplete',
                    attrs={'style': 'width: 100%'}
                ),
                label='New ' + position,
                required=True
            )
        for i in range(self.NUMBER_OF_OCMS):
            name = 'OCM #{0}'.format(i + 1)
            slug_name = slugify(name)
            self.fields[slug_name] = forms.ModelChoiceField(
                queryset=Member.objects.all(),
                widget=CrispyModelSelect2(
                    url='members:autocomplete',
                    attrs={'style': 'width: 100%'}
                ),
                label='New ' + name,
                required=True
            )

        super().__init__(self, skip_init=True)

    def clean(self):
        fields = list(map(slugify, self.NON_OCM_POSITIONS + ['OCM #'+str(i+1) for i in range(self.NUMBER_OF_OCMS)]))
        cleaned_new_committee_fields = {field_name: self.cleaned_data[field_name] for field_name in fields}

        # Check if the new committee fields are unique to each other.
        if len(cleaned_new_committee_fields.values()) != len(set(cleaned_new_committee_fields.values())):
            raise ValidationError('A committee cannot be submitted with duplicate members.', code='duplicate')

        # Check if all the new committee are actual members, and if the exec are guild members
        for field_name in cleaned_new_committee_fields:
            membership = cleaned_new_committee_fields[field_name].get_most_recent_membership()
            if membership is not None:
                if membership.expired is True:
                    self.add_error(field_name, "This member doesn't have a valid membership.")
                if 'ocm' not in field_name:
                    if membership.guild_member is False:
                        self.add_error(field_name, 'This member needs to be a guild member.')
            else:
                self.add_error(field_name, "This member doesn't have a valid membership.")

        # If IPP is ticked, so must the complete refresh
        if self.cleaned_data['include_ipp'] is True and self.cleaned_data['full_committee_change'] is False:
            self.add_error('include_ipp', "You can't include the IPP if it isn't a full committee changeover.")

    def submit(self, request):
        fields = list(map(slugify, self.NON_OCM_POSITIONS + ['OCM #' + str(i + 1) for i in range(self.NUMBER_OF_OCMS)]))
        cleaned_new_committee_fields = {field_name: self.cleaned_data[field_name] for field_name in fields}

        include_ipp = self.cleaned_data['include_ipp']
        full_committee_change = self.cleaned_data['full_committee_change']

        if full_committee_change is True:
            # Expire all old committee ranks (Committee + Position)
            # Then add in the new ones
            pass
            messages.success(request, 'Did the thing')
        else:
            # Expire only the old ranks (Position only)
            # Example, if the secretary quits, an OCM takes their place, and then a new OCM is elected
            # Then we:
            #   - expire the old secretary rank (Committee + Secretary)
            #   - expire the OCM rank, keep the Committee rank, and add the Secretary rank
            #   - add a new Committee and OCM rank to the incoming member.
            pass
