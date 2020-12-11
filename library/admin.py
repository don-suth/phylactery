from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes
from .forms import ItemTaggitForm


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    form = ItemTaggitForm

    class Media:
        # These scripts were going to load anyway,
        # but this needs to be here, otherwise
        # they'd load in the wrong order.
        js = [
            'admin/js/jquery.init.js',
            'autocomplete_light/jquery.init.js',
        ]


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
