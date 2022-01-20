from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) + str(user.is_active)
        )


class EmailPrefsTokenGenerator(PasswordResetTokenGenerator):
    # Token generator for Email Preference modifications
    # Members can request a new token at any time, they are valid for the default time.
    # (Three days by default)
    def _make_hash_value(self, member, timestamp):
        return (
            str(member.pk) + str(timestamp) + str(member.email_address)
        )


account_activation_token = AccountActivationTokenGenerator()
email_preference_token = EmailPrefsTokenGenerator()
