from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationEmail(forms.Form):
    # Form that handles initial registration
    # Only gatekeepers should be able to have accounts.
    reg_email = forms.EmailField(label="Email", max_length=100)


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
