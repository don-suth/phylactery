from django import forms


class RegistrationEmail(forms.Form):
    # Form that handles initial registration
    # Only gatekeepers should be able to have accounts.
    reg_email = forms.EmailField(label="Email", max_length=100)
