from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Rank, MemberFlag
import datetime
from django.db.models import Q


class MemberGatekeeperFilter(admin.SimpleListFilter):
    title = 'gatekeeper status:'
    parameter_name = 'gatekeeper'

    def lookups(self, request, model_admin):
        return (
            ('gate', 'Gatekeepers'),
            ('notgate', 'Non-gatekeepers'),
        )

    def queryset(self, request, queryset):
        today = datetime.date.today()
        if self.value() == 'gate':
            return queryset.filter(
                Q(ranks__expired_date__lte=today) | Q(ranks__expired_date=None),
                ranks__rank__rank_name="GATEKEEPER",
            )
        if self.value() == 'notgate':
            return queryset.exclude(
                Q(ranks__expired_date__lte=today) | Q(ranks__expired_date=None),
                ranks__rank__rank_name="GATEKEEPER",
            )


class MemberIsValidMemberFilter(admin.SimpleListFilter):
    title = 'membership status:'
    parameter_name = 'financial_member'

    def lookups(self, request, model_admin):
        return (
            ('financial', 'All Financial Members'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'financial':
            return queryset.filter(
                memberships__expired=False
            )


class MemberGatekeeperViewFilter(MemberGatekeeperFilter):
    # Exactly the same as the above but with a different template for outside of admin things.
    template = 'members/filter.html'


class MemberIsValidMemberViewFilter(MemberIsValidMemberFilter):
    template = 'members/filter.html'


class MemberListAdmin(admin.ModelAdmin):
    # This exists for the filter feature in members.views
    # While not used here, it is necessary.
    list_filter = (MemberGatekeeperViewFilter, MemberIsValidMemberViewFilter)
    search_fields = ('first_name', 'last_name', 'preferred_name')


class RanksInline(admin.TabularInline):
    model = Rank.member.through
    extra = 1


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fk_name = 'member'


class MemberFlagsInline(admin.TabularInline):
    model = MemberFlag.member.through
    extra = 4


class MemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'pronouns', 'email_address', 'student_number', 'join_date', 'is_fresher', 'notes')
    search_fields = ('first_name', 'last_name', 'preferred_name')
    list_filter = (MemberGatekeeperFilter,MemberIsValidMemberFilter)
    inlines = [MemberFlagsInline, MembershipInline, RanksInline]


class RanksAdmin(admin.ModelAdmin):
    inlines = [RanksInline]
    exclude = ('member',)


class MemberFlagsAdmin(admin.ModelAdmin):
    inlines = [MemberFlagsInline]
    exclude = ('member',)


admin.site.register(Member, MemberAdmin)
admin.site.register(Rank, RanksAdmin)
admin.site.register(Membership)
admin.site.register(MemberFlag, MemberFlagsAdmin)
