from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Button, HTML, Div


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

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
                    Button('submit', 'Submit', type='submit', css_class='btn-primary'),
                ),
                style="max-width: 576px", css_class="container"
            )
        )


class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control-lg"}))
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control-lg'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = 'account:login'
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    'Login',
                    HTML("""
                        <p>Gatekeepers and Committee members can login for more features.</p>
                    """),
                    'username',
                    'password',
                    Button('submit', 'Submit', type='submit', css_class='btn-primary'),
                ),
                style="max-width: 576px", css_class="container"
            )
        )
