from members.models import Member, Membership
import string

for char in string.ascii_uppercase[1:]:
    member_data = {
        'first_name': char,
        'last_name': '{0}member'.format(char),
        'pronouns': 'They/Them',
        'student_number': ord(char),
        'email_address': '{0}@{0}member.com'.format(char),
        'receive_emails': True
    }
    membership_data = {
        'guild_member': True,
        'phone_number': ord(char),
        'expired': False,
        'amount_paid': 7,
        'authorising_gatekeeper': None
    }
    new_member = Member(**member_data)
    new_membership = Membership(member=new_member, **membership_data)
    new_member.save()
    new_membership.save()