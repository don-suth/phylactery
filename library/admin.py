from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes, StrTag, StrTagValues, IntTagValues, IntTag, StaticTag


class StrTagValuesInline(admin.TabularInline):
    model = StrTagValues
    extra = 1


class IntTagValuesInline(admin.TabularInline):
    model = IntTagValues
    extra = 1


class StaticTagInline(admin.TabularInline):
    model = StaticTag.items.through
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"item_slug": ("item_name",)}
    inlines = (StrTagValuesInline, IntTagValuesInline, StaticTagInline)


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
admin.site.register(StrTag)
admin.site.register(IntTag)
admin.site.register(StaticTag)