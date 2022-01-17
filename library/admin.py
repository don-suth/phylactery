from django.contrib import admin

# Register your models here.
from .models import Item, BorrowRecord, ExternalBorrowingForm, ExternalBorrowingItemRecord, \
    ItemBaseTags, ItemComputedTags, TagParent
from .forms import ItemTaggitForm, BaseTagForm, ComputedTagForm


class ItemBaseTagInline(admin.TabularInline):
    model = ItemBaseTags
    form = BaseTagForm


class ItemComputedTagInline(admin.TabularInline):
    model = ItemComputedTags
    form = ComputedTagForm
    readonly_fields = ('computed_tags',)


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
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
    filter_horizontal = ('parent_tag',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()


class ExternalBorrowingItemRecordAdmin(admin.TabularInline):
    model = ExternalBorrowingItemRecord
    extra = 1


class ExternalBorrowingFormAdmin(admin.ModelAdmin):
    model = ExternalBorrowingForm
    inlines = [ExternalBorrowingItemRecordAdmin]



admin.site.register(Item, ItemAdmin)
admin.site.register(BorrowRecord)
admin.site.register(ExternalBorrowingForm, ExternalBorrowingFormAdmin)
admin.site.register(TagParent, TagParentAdmin)
