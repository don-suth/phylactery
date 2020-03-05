from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Rank, Interest

class RanksInline(admin.TabularInline):
    model = Rank.member.through
    extra = 1

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0

class InterestInline(admin.TabularInline):
    model = Interest.member.through
    extra = 4

class MemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'pronouns', 'email_address', 'student_number', 'join_date', 'is_fresher', 'notes')
    inlines = [InterestInline, MembershipInline, RanksInline]

class RanksAdmin(admin.ModelAdmin):
    inlines = [RanksInline]
    exclude = ('member',)

class InterestsAdmin(admin.ModelAdmin):
    inlines = [InterestInline]
    exclude = ('member',)


admin.site.register(Member, MemberAdmin)
admin.site.register(Rank, RanksAdmin)
admin.site.register(Membership)
admin.site.register(Interest, InterestsAdmin)