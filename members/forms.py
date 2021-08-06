from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm, UsernameField,
    PasswordChangeForm, PasswordResetForm, _unicode_ci_compare,
    SetPasswordForm
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.template import loader
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, PrependedText
from .models import MemberFlag, UnigamesUser
from phylactery.tasks import send_single_email_task, compose_html_email

number_validator = RegexValidator(regex=r"^[0-9]+$")
no_student_number = RegexValidator(
    regex=r"@student\.uwa\.edu\.au",
    message="Your email cannot be a student email.",
    inverse_match=True
)


class OldMembershipForm(forms.Form):
    first_name = forms.CharField(
        required=True,
        max_length=200,
    )
    last_name = forms.CharField(
        required=True,
        max_length=200,
    )
    preferred_name = forms.CharField(
        required=False,
        label="Preferred Name (leave blank if your first name is fine)",
        max_length=200,
    )
    pronouns = forms.CharField(
        widget=forms.TextInput(
            attrs={"id": "pronounField", "placeholder": "Type your own here"}
        ),
        required=False,
        label="Pronouns (Type your own, or use the preset ones &#9660;)",
        max_length=200,
    )
    is_guild = forms.BooleanField(
        required=False,
        label="Are you a current Guild Member?"
    )
    student_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"type": "tel"}),
        validators=[number_validator],
        max_length=10,
    )
    email = forms.EmailField(
        required=True,
        validators=[no_student_number],
        label='Non-Student Email: '
    )
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"type": "tel"}),
        validators=[number_validator]
    )
    receive_emails = forms.BooleanField(
        required=False,
        label="Would you like to receive emails from us?"
    )
    amount_paid = forms.IntegerField(
        min_value=0,
        max_value=20,
        required=True,
        label="How much has this member paid for Membership?"
    )
    sticker_received = forms.BooleanField(
        required=True,
        label="Has the member received their sticker?"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_fields = []
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Become a member of Unigames!',
                    Div(
                        Div(
                            'first_name',
                            css_class="col"
                        ),
                        Div(
                            'last_name',
                            css_class="col"
                        ),
                        css_class="form-row"
                    ),
                    'preferred_name',
                    FieldWithButtons(
                        'pronouns',
                        StrictButton(
                            "He / Him",
                            css_class="btn-outline-secondary",
                            onclick='$("#pronounField").val("He / Him")'
                        ),
                        StrictButton(
                            "She / Her",
                            css_class="btn-outline-secondary",
                            onclick='$("#pronounField").val("She / Her")'
                        ),
                        StrictButton(
                            "They / Them",
                            css_class="btn-outline-secondary",
                            onclick='$("#pronounField").val("They / Them")'
                        ),
                    ),
                    'is_guild',
                    'student_number',
                    'email',
                    'receive_emails',
                    'phone_number',
                ),
                Div(
                    Div(
                        Div(
                            Div(
                                HTML('''<h5 class="modal-title" id="confirmModalLabel">
                                Please pass the device back to {{ user.member.first_name }}.</h5>'''),
                                StrictButton('&times;', css_class='btn-close', data_dismiss='modal', aria_label='Close'),
                                css_class="modal-header"
                            ),
                            Div(
                                HTML('''
                                <p>{{ user.member.first_name }}, please fill out the following:</p>
                                <p>Note: Make sure this process is 100% done and the form is 
                                submitted before the member departs.</p>
                                '''),
                                PrependedText('amount_paid', '$'),
                                'sticker_received',
                                HTML('''
                                <p>By clicking the submit button below, you ({{ user.member.first_name }})
                                verify that this information is correct to the best of your knowledge.'''),
                                css_class="modal-body"
                            ),
                            Div(
                                StrictButton('Close', css_class='btn-secondary', data_dismiss='modal'),
                                Submit('submit', 'Save Changes and Submit', css_class='btn-primary'),
                                css_class="modal-footer"
                            ),
                            css_class="modal-content"
                        ),
                        css_class="modal-dialog"
                    ),
                    css_class="modal fade", css_id="confirmModal", aria_labelledby="confirmModalLabel", tabindex="-1",
                    aria_hidden="true",
                ),
                StrictButton('Submit', css_class='btn-primary', data_toggle='modal', data_target='#confirmModal'),
                style="max-width: 576px", css_class="container"
            )
        )
        for flag in MemberFlag.objects.filter(active=True):
            field_name = 'flag_' + str(flag.pk)
            self.extra_fields.append(flag.pk)
            self.fields[field_name] = forms.BooleanField(label=flag.description, required=False)
            self.helper.layout[0][0].append(field_name)

    def clean(self):
        cleaned_data = super().clean()
        is_guild = cleaned_data.get('is_guild')
        student_number = cleaned_data.get('student_number')
        amount_paid = cleaned_data.get('amount_paid')
        if is_guild is True and not student_number:
            self.add_error('student_number', 'If you are a guild member, a student number is required.')
        if is_guild is True and amount_paid is not None and amount_paid != 5:
            self.add_error('is_guild', 'If you are a guild member, you should be paying $5')
            self.add_error('amount_paid', 'If you are a guild member, you should be paying $5')
        if is_guild is False and amount_paid is not None and amount_paid != 7:
            self.add_error('is_guild', "If you aren't a guild member, you should be paying $7")
            self.add_error('amount_paid', "If you aren't a guild member, you should be paying $7")


class NewMembershipForm(OldMembershipForm):
    is_fresher = forms.BooleanField(
        required=False,
        initial=True,
        label='Is this member a fresher?'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout[0][1][0][0][1].insert(3, 'is_fresher')



class SignupForm(UserCreationForm):
    """
    Renders the signup form for gatekeepers.
    """
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError("The given email is already registered.")
        return self.cleaned_data['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = 'account:signup'
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Sign Up',
                    HTML("""
                        <p>Only Unigames Gatekeepers and Committee members can sign up for an account to 
                        access special features.</p>
                        <p>If you aren't a Gatekeeper or Committee member, this form won't do anything.</p>
                        <p>If you are a Unigames Gatekeeper, and wish to create an account, you may begin the account 
                        creation process by entering your email address below.</p>
                    """),
                    'username',
                    'email',
                    'password1',
                    'password2',
                    Submit('submit', 'Submit', css_class='btn-primary'),
                ),
                style="max-width: 576px", css_class="container"
            )
        )


class LoginForm(AuthenticationForm):
    """
    Renders the login form.
    """
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control-lg"}))
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control-lg'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Login',
                    HTML("""
                        <p>Gatekeepers and Committee members can login for more features.</p>
                        <p>Don't have an account yet? You might want to 
                        <a href="{% url 'account:signup' %}">Sign Up</a>.</p>
                    """),
                    'username',
                    'password',
                    Submit('submit', 'Submit', css_class='btn-primary'),
                ),
                style="max-width: 576px", css_class="container"
            )
        )


class MyPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Change Password',
                    HTML("""
                        <p>To change your password, enter your old password, 
                        and your new password twice to confirm.</p>
                    """),
                    'old_password',
                    'new_password1',
                    'new_password2',
                    Submit('submit', 'Submit', css_class='btn-primary'),
                )
            )
        )


class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
        required=False
    )
    username = forms.CharField(
        label='Username',
        max_length=254,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Reset Password',
                    HTML("""
                        <p>To reset your password, 
                        enter your email address or your username below.</p>
                    """),
                    'email',
                    'username',
                    Submit('submit', 'Submit', css_class='btn-primary'),
                )
            )
        )

    def clean(self):
        if not (self.cleaned_data['username'] or self.cleaned_data['email']):
            raise ValidationError('Exactly one of the username or email fields must be submitted.')
        if self.cleaned_data['username'] and self.cleaned_data['email']:
            raise ValidationError('Only one of the email or username fields should be filled out.')

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):

        message, html_message = compose_html_email('account/password_reset_email.html', context)

        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        send_single_email_task.delay(to_email, subject, message, html_message=html_message)


    @staticmethod
    def get_user_by_username(username):
        active_users = UnigamesUser.objects.filter(
            username__iexact=username,
            member__isnull=False,
            is_active=True
        )
        valid_users = [
            u for u in active_users
            if u.has_usable_password() and
            _unicode_ci_compare(u.username, username)
        ]
        if len(valid_users) == 1:
            return valid_users
        return []

    @staticmethod
    def get_user_by_email(email):
        active_users = UnigamesUser.objects.filter(
            is_active=True,
            member__isnull=False,
            email__iexact=email
        )
        valid_users = [
            u for u in active_users
            if u.has_usable_password() and
            _unicode_ci_compare(u.email, email)
        ]
        if len(valid_users) == 1:
            return valid_users
        return []

    def get_users(self, *args):
        # Overrides the default method to use our method.
        # We don't care about the *args, we just use the cleaned data
        users = []
        if self.cleaned_data['email']:
            users = self.get_user_by_email(self.cleaned_data['email'])
        elif self.cleaned_data['username']:
            users = self.get_user_by_username(self.cleaned_data['username'])
        return users


class MySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Set your new password',
                    HTML("""
                            <p>Please enter your new password twice so we can verify you typed it in correctly.</p>    
                        """),
                    'new_password1',
                    'new_password2',
                    Submit('submit', 'Submit', css_class='btn-primary'),
                )
            )
        )