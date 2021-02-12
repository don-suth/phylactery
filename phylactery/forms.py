from members.models import Member, UnigamesUser, Rank, RankAssignments, MemberFlag
from django import forms
from django.core.exceptions import ImproperlyConfigured
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, PrependedText


class ControlPanelForm(forms.Form):
    # Base class for control panel forms.
    # Control panel forms should:
    # - have a submit function that does their thing
    # - define self.helper.form_action
    # - define self.helper.layout

    form_tag = True
    form_method = 'post'
    form_action = None
    layout = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = self.form_tag
        self.helper.form_method = self.form_method
        if self.form_action is not None:
            self.helper.form_action = self.form_action
        else:
            raise ImproperlyConfigured('You must define a form action')
        if self.layout is not None:
            self.helper.layout = self.layout
        else:
            raise ImproperlyConfigured('You must define a form layout')



class PurgeAllGatekeepers(ControlPanelForm):
    # When submitted, removes the gatekeeper rank from all non-committee members
    form_action = 'phylactery:control-1'
    layout = Layout(
        Fieldset(
            'Purge all Gatekeepers',
            HTML('''<p>This button will remove the gatekeeper status of all non-committee gatekeepers.'''),
            Submit('submit', 'Purge!', css_class='btn-primary'),
        )
    )

    def submit(self):
        # Do the thing!
        pass
