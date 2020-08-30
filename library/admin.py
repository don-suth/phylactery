from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes, StrTag, StrTagValues, IntTagValues, IntTag, StaticTag


class StrTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class IntTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class StaticTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class StrTagValuesInline(admin.TabularInline):
    model = StrTagValues
    autocomplete_fields = ('tag',)
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
    inlines = (StrTagValuesInline, IntTagValuesInline, StaticTagInline)


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
admin.site.register(StrTag, StrTagAdmin)
admin.site.register(IntTag, IntTagAdmin)
admin.site.register(StaticTag, StaticTagAdmin)
