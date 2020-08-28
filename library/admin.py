from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes, StrTag, StrTagValues, IntTagValues, IntTag, StaticTag


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"item_slug": ("item_name",)}


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
admin.site.register(StrTag)
admin.site.register(IntTag)
admin.site.register(StaticTag)
admin.site.register(IntTagValues)
admin.site.register(StrTagValues)