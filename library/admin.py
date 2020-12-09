from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes
from .forms import ItemTaggitForm


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    form = ItemTaggitForm

    class Media:
        js = [
            'admin/js/jquery.init.js',
            'autocomplete_light/jquery.init.js',
        ]


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
