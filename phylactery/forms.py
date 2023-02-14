from members.models import Member, UnigamesUser, Rank, RankAssignments, MemberFlag, Membership
from library.forms import CrispyModelSelect2, CrispyModelSelect2Multiple
from django import forms
from django.core.exceptions import ImproperlyConfigured
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, PrependedText, Accordion, AccordionGroup
from django.utils.text import slugify
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.contrib.admin import widgets
from django.shortcuts import reverse
from django.forms import ValidationError
from django.contrib import messages
from django.db.models import Q
import datetime
import warnings


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

def expire_specific_ranks(member, rank_name):
    today = datetime.date.today()
    ranks = RankAssignments.objects \
        .exclude(expired_date__lte=today) \
        .filter(rank__rank_name__iexact=rank_name, member=member) \
        .order_by('assignment_date')
    if ranks.exists():
        for assignment in ranks:
            assignment.expire()


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
        return date

    def submit(self, request):
        memberships_to_expire = Membership.objects.filter(
            date__lt=self.cleaned_data['cut_off_date'],
            expired=False
        )
        expired_memberships = len(memberships_to_expire)
        for membership in memberships_to_expire:
            membership.expired = True
            membership.save()
        if expired_memberships:
            messages.success(
                request,
                'Successfully invalidated {0} membership{1}'
                    .format(expired_memberships, 's' if expired_memberships > 1 else '')
            )
        else:
            messages.warning(request, 'No memberships to expire.')

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

    gatekeepers_to_add = forms.ModelMultipleChoiceField(
        queryset=Member.objects.all(),
        widget=CrispyModelSelect2Multiple(url='members:autocomplete', attrs={'style': 'width:100%'})
    )

    def get_layout(self):
        return Layout(
            'gatekeepers_to_add'
        )

    def submit(self, request):
        already_gatekeeper = []
        success_gatekeeper = []
        for member in self.cleaned_data['gatekeepers_to_add']:
            if member.has_rank('GATEKEEPER'):
                already_gatekeeper.append(str(member))
                continue
            member.add_rank('GATEKEEPER')
            success_gatekeeper.append(str(member))
        if already_gatekeeper:
            messages.warning(request, 'The following members were already gatekeepers: '+', '.join(already_gatekeeper))
        if success_gatekeeper:
            messages.success(request, 'The following members were successfully added as gatekeepers: '+', '.join(success_gatekeeper))


class MakeWebkeepers(ControlPanelForm):
    form_name = 'Promote Members to Webkeepers'
    form_description = 'Promotes the selected members to webkeepers.'
    form_media = True

    form_permissions = ['President', 'Vice-President', 'Secretary']

    webkeepers_to_add = forms.ModelMultipleChoiceField(
        queryset=Member.objects.all(),
        widget=CrispyModelSelect2Multiple(url='members:autocomplete', attrs={'style': 'width:100%'})
    )

    def get_layout(self):
        return Layout(
            'webkeepers_to_add'
        )

    def submit(self, request):
        already_webkeeper = []
        success_webkeeper = []
        for member in self.cleaned_data['webkeepers_to_add']:
            if member.has_rank('WEBKEEPER'):
                already_webkeeper.append(str(member))
                continue
            member.add_rank('WEBKEEPER')
            success_webkeeper.append(str(member))
        if already_webkeeper:
            messages.warning(request, 'The following members were already webkeepers: '+', '.join(already_webkeeper))
        if success_webkeeper:
            messages.success(request, 'The following members were successfully added as webkeepers: '+', '.join(success_webkeeper))

class AddRemoveRanks(ControlPanelForm):
    form_name = 'Selectively Add or Remove Ranks'
    form_description = 'Gives or Removes ranks for a single member. '\
                       'Useful for removing the Gatekeeper rank from a single member. '
    form_long_description = 'This form cannot be used for committee rank transfer. ' \
                            'Use the Committee Transfer Form for that.'
    form_media = True

    form_permissions = ['President', 'Vice-President', 'Secretary']

    member_to_alter = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=CrispyModelSelect2(url='members:autocomplete', attrs={'style': 'width:100%'})
    )

    add_or_remove = forms.ChoiceField(
        choices=[('ADD', 'Add Rank'), ('REMOVE', 'Remove Rank')],
        widget=forms.RadioSelect
    )

    rank_to_alter = forms.ModelChoiceField(
        queryset=Rank.objects.filter(rank_name__in=['EXCLUDED', 'GATEKEEPER', 'WEBKEEPER', 'LIFE-MEMBER']),
        widget=CrispyModelSelect2(attrs={'style':'width:100%'})
    )

    def get_layout(self):
        return Layout(
            'member_to_alter',
            'add_or_remove',
            'rank_to_alter'
        )

    def submit(self, request):
        clean_member, clean_rank, clean_mode = self.cleaned_data['member_to_alter'], \
            self.cleaned_data['rank_to_alter'], self.cleaned_data['add_or_remove']
        if clean_mode == 'ADD':
            # Check if the member has that rank already.
            if clean_member.has_rank(clean_rank.rank_name):
                messages.warning(request, '{0} was already {1}'.format(clean_member, clean_rank))
            else:
                clean_member.add_rank(clean_rank.rank_name)
                messages.success(request, '{0} was successfully made {1}'.format(clean_member, clean_rank))
        elif clean_mode == 'REMOVE':
            # Check if they are that rank
            if clean_member.has_rank(clean_rank.rank_name):
                expire_specific_ranks(clean_member, clean_rank.rank_name)
                messages.success(request, '{0} successfully had their {1} rank removed.'.format(clean_member, clean_rank))
            else:
                messages.warning(request, '{0} already did not have the {1} rank.'.format(clean_member, clean_rank))

class CommitteeTransfer(ControlPanelForm):
    form_name = 'Committee Transfer'
    form_description = 'Freely transfer committee roles.'
    form_long_description = \
        """For each committee position, you can either decide to keep the position as-is, assign a new person to that 
        position, or remove that person from the position without a replacement."""
    form_permissions = ['President', 'Vice-President']

    NUMBER_OF_OCMS = 4

    COMMITTEE_POSITIONS = [
        'President',
        'Vice-President',
        'Treasurer',
        'Secretary',
        'Librarian',
        'Fresher-Rep',
        'OCM',
        'IPP',
    ]

    RADIO_CHOICES = [
        ('retain', 'Retain previous committee member'),
        ('elect', 'Elect new committee member'),
        ('remove', 'Remove the committee member from this position, with no replacement')
    ]

    def get_current_committee(self, flat=False):
        # Find all current committee members
        # Returns a dictionary, keyed with committee rank and a list of members with that rank.
        # There should only be one committee member of each rank, plus some OCMs
        today = datetime.date.today()
        if flat is False:
            committee = {}
            for position in self.COMMITTEE_POSITIONS:
                # Find the member(s) with the most recent non-expired rank
                committee[position] = Member.objects.filter(
                    Q(ranks__expired_date__gt=today) | Q(ranks__expired_date=None),
                    ranks__rank__rank_name=position.upper()
                ).order_by('pk')
        else:
            # A different format: Just returns the list of all committee members, without their positions.
            committee = []
            for position in self.COMMITTEE_POSITIONS:
                committee_members = Member.objects.filter(
                    Q(ranks__expired_date__gt=today) | Q(ranks__expired_date=None),
                    ranks__rank__rank_name=position.upper()
                )
                committee.append(committee_members)
        return committee

    def check_valid_for_position(self, field, member, position):
        # Returns True if the given member is eligible for the position.
        # All committee members have to have a valid membership.
        # Execs also have to be guild members.
        exec_positions = [
            'President',
            'Vice-President',
            'Treasurer',
            'Secretary',
            'Librarian'
        ]
        if member is None:
            self.add_error(field, "You haven't selected anyone to elect to this position.")
            return False
        membership = member.get_most_recent_membership()
        if membership is None or membership.expired is True:
            # Obviously not valid
            self.add_error(field, "This member doesn't have a valid membership.")
            return False
        if member.student_number == "" or member.student_number is None:
            # As of Feb 13th 2023, all Committee Members must be students.
            # (This is checked for by requiring a student number)
            self.add_error(field, "This member doesn't appear to be a student.")
            return False
        if position in exec_positions and membership.guild_member is False:
            self.add_error(field, "This member is not currently a Guild member.")
            return False
        else:
            return True

    def check_for_duplicate_committee_members(self, committee):
        # Given a dict of committee positions and members,
        duplicate_check = []
        duplicates = []

        for position in self.COMMITTEE_POSITIONS:
            for committee_member in committee[position]:
                if committee_member in duplicate_check and committee_member not in duplicates:
                    duplicates.append(committee_member)
                else:
                    duplicate_check.append(committee_member)

        return duplicates

    def check_for_committee_differences(self, old_committee, new_committee):
        committee_changes = []
        # To this list, we append sub-lists, of the form [Member, old_position, new_position]
        # If old_position is None, they are a new member to committee.
        # If new_position is None, they are leaving committee.

        def find_committee_member_index(member):
            # Searches committee_changes for the specified member.
            # Returns the index, or -1 if they aren't there.
            for i in range(len(committee_changes)):
                if committee_changes[i][0] == member:
                    return i
            return -1

        for position in self.COMMITTEE_POSITIONS:
            for committee_member in old_committee[position]:
                committee_changes.append([committee_member, position, None])
        for position in self.COMMITTEE_POSITIONS:
            for committee_member in new_committee[position]:
                # Check if they're already in the changelist
                committee_index = find_committee_member_index(committee_member)
                if committee_index != -1:
                    # They're here, change the new_position
                    committee_changes[committee_index][2] = position
                else:
                    # They're new, put them in.
                    committee_changes.append([committee_member, None, position])

        return committee_changes

    def __init__(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)

        self.cleaned_new_committee = None
        self.cleaned_current_committee = None

        current_committee = self.get_current_committee()

        for position in self.COMMITTEE_POSITIONS:
            if position == 'OCM':
                number_of_repeats = self.NUMBER_OF_OCMS
            else:
                number_of_repeats = 1

            for i in range(number_of_repeats):
                if number_of_repeats == 1:
                    slug_name = slugify(position)
                else:
                    slug_name = slugify(position+str(i+1))

                assigned_field_name = 'assigned_' + slug_name
                try:
                    initial_val = current_committee[position][i]
                except IndexError:
                    initial_val = None
                self.fields[assigned_field_name] = forms.ModelChoiceField(
                    queryset=Member.objects.all(),
                    widget=CrispyModelSelect2(
                        url='members:autocomplete',
                        attrs={'style': 'width: 100%',}
                    ),
                    label='Assigned ' + position,
                    required=False,
                    initial=initial_val
                )
                radio_field_name = 'options_' + slug_name
                self.fields[radio_field_name] = forms.ChoiceField(
                    widget=forms.RadioSelect,
                    choices=self.RADIO_CHOICES,
                    label="",
                    initial='retain'
                )

        super().__init__(self, skip_init=True)

    def get_layout(self):
        layout = Layout()
        current_committee = self.get_current_committee()
        layout.append(HTML('<p>Current Committee:</p><ul>'))

        for position in self.COMMITTEE_POSITIONS:
            layout.append(HTML('<li>' + position + '<ul>'))
            if len(current_committee[position]) == 0:
                layout.append(HTML('<li>None</li>'))
            else:
                for committee_member in current_committee[position]:
                    layout.append(HTML('<li>' + str(committee_member) + '</li>'))
            layout.append(HTML('</ul></li>'))

        layout.append(HTML('</ul>'))
        new_accordion = Accordion()
        for position in self.COMMITTEE_POSITIONS:
            if position == 'OCM':
                number_of_repeats = self.NUMBER_OF_OCMS
            else:
                number_of_repeats = 1

            for i in range(number_of_repeats):
                if number_of_repeats == 1:
                    slug_name = slugify(position)
                    legend_title = position
                else:
                    slug_name = slugify(position+str(i+1))
                    legend_title = position + ' #' + str(i+1)

                assigned_field_name = 'assigned_' + slug_name
                radio_field_name = 'options_' + slug_name

                new_accordion.append(
                    AccordionGroup(
                        legend_title,
                        Field(radio_field_name),
                        Field(assigned_field_name),
                    )
                )
        layout.append(new_accordion)
        return layout

    def clean(self):
        # We need to check that:there are no duplicate members.
        # While doing so, we'll also get the data ready and cleaned up.
        super().clean()

        new_committee = {}
        old_committee = self.get_current_committee()

        for position in self.COMMITTEE_POSITIONS:
            if position != "OCM":
                # Only one member of each position

                slug_name = slugify(position)
                assigned_field_name = 'assigned_' + slug_name
                radio_field_name = 'options_' + slug_name

                if self.cleaned_data[radio_field_name] == 'retain':
                    new_committee[position] = old_committee[position]
                elif self.cleaned_data[radio_field_name] == 'remove':
                    new_committee[position] = []
                elif self.cleaned_data[radio_field_name] == 'elect':
                    position_elect = self.cleaned_data[assigned_field_name]
                    if self.check_valid_for_position(assigned_field_name, position_elect, position):
                        new_committee[position] = [position_elect]

            elif position == "OCM":
                new_committee[position] = []

                for i in range(self.NUMBER_OF_OCMS):
                    # Have to handle multiples

                    slug_name = slugify(position + str(i + 1))
                    assigned_field_name = 'assigned_' + slug_name
                    radio_field_name = 'options_' + slug_name

                    number_of_current_ocms = len(old_committee[position])

                    if self.cleaned_data[radio_field_name] == 'retain':
                        # Old committee and the form will generate the list of OCMs in the same order
                        # So we can just use the old committee list.
                        if i < number_of_current_ocms:
                            new_committee[position].append(old_committee[position][i])
                        else:
                            pass
                    elif self.cleaned_data[radio_field_name] == 'remove':
                        # We just skip this field entirely.
                        pass
                    elif self.cleaned_data[radio_field_name] == 'elect':
                        position_elect = self.cleaned_data[assigned_field_name]
                        if self.check_valid_for_position(assigned_field_name, position_elect, position):
                            new_committee[position].append(position_elect)

        errors = []
        for duplicate in self.check_for_duplicate_committee_members(new_committee):
            errors.append(
                ValidationError(
                    "%(member) is listed more than once in the new committee.",
                    params={'member', str(duplicate)},
                    code='duplicate'
                )
            )
        if errors:
            raise ValidationError(errors)

        self.cleaned_new_committee = new_committee
        self.cleaned_current_committee = old_committee

        return new_committee

    def submit(self, request):
        success_add = []
        success_remove = []
        success_change = []
        changelist = self.check_for_committee_differences(self.cleaned_current_committee, self.cleaned_new_committee)

        for member, old_position, new_position in changelist:
            # If the old_position and new_position is the same, we ignore it.
            if old_position == new_position:
                pass
            # If the old_position is None, then we add them to committee.
            elif old_position is None and new_position is not None:
                member.add_rank('COMMITTEE')
                member.add_rank(new_position)
                success_add.append(conditional_escape('appointed {0} to {1}'.format(member, new_position)))
            # If it's the other way around, then we remove them from committee.
            elif new_position is None and old_position is not None:
                committee_rank = member.get_recent_rank('COMMITTEE')
                position_rank = member.get_recent_rank(old_position)
                if committee_rank:
                    committee_rank.expire()
                if position_rank:
                    position_rank.expire()
                if committee_rank or position_rank:
                    success_remove.append(conditional_escape('{0}, from {1}'.format(member, old_position)))
            # Otherwise we remove their old position and put in the new one.
            elif old_position is not None and new_position is not None:
                position_rank = member.get_recent_rank(old_position)
                if position_rank:
                    position_rank.expire()
                member.add_rank(new_position)
                # Double check that they have the committee rank.
                committee_rank = member.get_recent_rank('COMMITTEE')
                if committee_rank is None:
                    member.add_rank('COMMITTEE')
                success_change.append(conditional_escape('{0}, from {1} to {2}'.format(member, old_position, new_position)))
        success_message = ''
        if success_remove:
            success_message += 'Successfully removed the following committee members:<uL>'
            for removal in success_remove:
                success_message += '<li>'+removal+'</li>'
            success_message += '</ul>'
        if success_change:
            success_message += 'Successfully changed the following committee positions:<ul>'
            for change in success_change:
                success_message += '<li>'+change+'</li'
            success_message += '</ul>'
        if success_add:
            success_message += 'Successfully added the following members to committee:<ul>'
            for addition in success_add:
                success_message += '<li>'+addition+'</li>'
            success_message += '</ul>'
        success_message = mark_safe(success_message)
        messages.success(request, success_message)
