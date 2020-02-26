from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Rank

class MemberAdmin(admin.ModelAdmin):
    list_display = ('preferred_name', 'last_name', 'join_date', 'is_fresher')


admin.site.register(Member, MemberAdmin)
admin.site.register(Membership)
admin.site.register(Rank)