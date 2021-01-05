from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from .models import MemberFlag

number_validator = RegexValidator(regex=r"^[0-9]+$")
no_student_number = RegexValidator(
    regex=r"@student\.uwa\.edu\.au",
    message="Your email cannot be a student email.",
    inverse_match=True
)


class MembershipForm(forms.Form):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                Submit('submit', 'Submit', css_class='btn-primary'),
                style="max-width: 576px", css_class="container"
            )
        )
        for flag in MemberFlag.objects.all():
            field_name = 'flag' + str(flag.pk)
            self.fields[field_name] = forms.BooleanField(label=flag.description, required=False)
            self.helper.layout[0][0].append(field_name)

    def clean(self):
        cleaned_data = super().clean()
        is_guild = cleaned_data.get('is_guild')
        student_number = cleaned_data.get('student_number')
        email = cleaned_data.get('email')
        if is_guild is True and not student_number:
            self.add_error('student_number', 'If you are a guild member, a student number is required.')


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
