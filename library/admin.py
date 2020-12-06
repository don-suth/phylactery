from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes, StrTag, StrTagValue, StrTagThrough, IntTagValues, IntTag, StaticTag
from .forms import StrTagThroughForm, ItemTaggitForm


class StrTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class IntTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class StaticTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class StrTagValueAdmin(admin.ModelAdmin):
    search_fields = ('value',)


class StrTagThroughInline(admin.TabularInline):
    model = StrTagThrough
    autocomplete_fields = ('tag',)
    form = StrTagThroughForm
    extra = 1


class IntTagValuesInline(admin.TabularInline):
    model = IntTagValues
    autocomplete_fields = ('tag',)
    extra = 1


class StaticTagInline(admin.TabularInline):
    model = StaticTag.items.through
    autocomplete_fields = ('statictag',)
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"item_slug": ("item_name",)}
    form = ItemTaggitForm
    inlines = (StrTagThroughInline, IntTagValuesInline, StaticTagInline)


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
admin.site.register(StrTag, StrTagAdmin)
admin.site.register(StrTagValue, StrTagValueAdmin)
admin.site.register(IntTag, IntTagAdmin)
admin.site.register(StaticTag, StaticTagAdmin)
