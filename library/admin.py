from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes, StrTag, StrTagValues, IntTagValues, IntTag, StaticTag


admin.site.register(Item)
admin.site.register(ItemTypes)
admin.site.register(StrTag)
admin.site.register(IntTag)
admin.site.register(StaticTag)
admin.site.register(IntTagValues)
admin.site.register(StrTagValues)