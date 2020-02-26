from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Rank

class MemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'pronouns', 'email_address', 'student_number', 'join_date', 'is_fresher', 'notes')


admin.site.register(Member, MemberAdmin)
admin.site.register(Membership)
admin.site.register(Rank)