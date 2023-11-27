from django.contrib import admin

# Register your models here.
from .models import Item, BorrowRecord, ExternalBorrowingForm, ExternalBorrowingItemRecord, \
    ItemBaseTags, ItemComputedTags, TagParent, Reservation
from .forms import ItemTaggitForm, BaseTagForm, ComputedTagForm


class ItemBaseTagInline(admin.TabularInline):
    model = ItemBaseTags
    form = BaseTagForm
    verbose_name = 'item base tags'
    verbose_name_plural = 'item base tags'


class ItemComputedTagInline(admin.TabularInline):
    model = ItemComputedTags
    form = ComputedTagForm
    readonly_fields = ('computed_tags',)
    verbose_name = 'item computed tags'
    verbose_name_plural = 'item computed tags'


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']
    form = ItemTaggitForm
    inlines = [ItemBaseTagInline, ItemComputedTagInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()

    class Media:
        # These scripts were going to load anyway,
        # but this needs to be here, otherwise
        # they'd load in the wrong order.

        pass
        #js = [
        #    'admin/js/jquery.init.js',
        #    'autocomplete_light/jquery.init.js',
        #]


class TagParentAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    ordering = ('child_tag',)
    search_fields = ('child_tag__name',)
    filter_horizontal = ('parent_tag',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()


class ExternalBorrowingItemRecordAdmin(admin.TabularInline):
    model = ExternalBorrowingItemRecord
    extra = 0
    readonly_fields = [
        'item',
        'borrower_name', 'auth_gatekeeper_borrow', 'date_borrowed',
        'returner_name', 'auth_gatekeeper_return', 'date_returned',
    ]

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ExternalBorrowingFormAdmin(admin.ModelAdmin):
    model = ExternalBorrowingForm
    inlines = [ExternalBorrowingItemRecordAdmin]
    readonly_fields = [
        'applicant_name', 'applicant_org', 'event_details',
        'contact_phone', 'contact_email', 'form_submitted_date',
        'requested_borrow_date', 'form_status', 'due_date',
        'librarian_comments',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReservationItems(admin.TabularInline):
    verbose_name = "Reserved item"
    model = Item.reservations.through
    extra = 0
    readonly_fields = ["item"]

    def has_delete_permission(self, request, obj=None):
        return False


class ReservationBorrowRecords(admin.TabularInline):
    verbose_name = "Associated borrow record"
    model = BorrowRecord.reservations.through
    extra = 0
    readonly_fields = ["borrowrecord"]

    def has_delete_permission(self, request, obj=None):
        return False


class ReservationAdmin(admin.ModelAdmin):
    model = Reservation
    readonly_fields = ['submitted_datetime', 'is_external', 'internal_member', 'status_update_datetime']
    fields = [
        'submitted_datetime',
        ('is_external', 'internal_member'),
        'borrower_name',
        'contact_email',
        'contact_info',
        ('date_to_borrow', 'date_to_return'),
        'additional_details',
        ('approval_status', 'status_update_datetime'),
        'librarian_comments',
        'active',
    ]

    def get_fields(self, request, obj=None):
        if obj.is_external:
            return [
                'submitted_datetime',
                'is_external',
                'borrower_name',
                'contact_email',
                'contact_info',
                ('date_to_borrow', 'date_to_return'),
                'additional_details',
                ('approval_status', 'status_update_datetime'),
                'librarian_comments',
                'active',
            ]
        else:
            return [
                'submitted_datetime',
                ('is_external', 'internal_member'),
                'borrower_name',
                'contact_email',
                'contact_info',
                ('date_to_borrow', 'date_to_return'),
                'additional_details',
                ('approval_status', 'status_update_datetime'),
                'librarian_comments',
                'active',
            ]

    inlines = [ReservationItems, ReservationBorrowRecords]


admin.site.register(Item, ItemAdmin)
admin.site.register(BorrowRecord)
admin.site.register(ExternalBorrowingForm, ExternalBorrowingFormAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(TagParent, TagParentAdmin)
