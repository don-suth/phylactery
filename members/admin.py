from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Rank

class RanksInline(admin.TabularInline):
    model = Rank.member.through
    extra = 1

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1

class MemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'pronouns', 'email_address', 'student_number', 'join_date', 'is_fresher', 'notes')
    inlines = [MembershipInline, RanksInline]

class RanksAdmin(admin.ModelAdmin):
    inlines = [RanksInline]
    exclude = ('member',)


admin.site.register(Member, MemberAdmin)
admin.site.register(Rank, RanksAdmin)