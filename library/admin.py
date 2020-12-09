from django.contrib import admin

# Register your models here.
from .models import Item, ItemTypes
from .forms import ItemTaggitForm
from taggit.models import Tag


class StrTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class IntTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class StaticTagAdmin(admin.ModelAdmin):
    search_fields = ('tag_name',)


class StrTagValueAdmin(admin.ModelAdmin):
    search_fields = ('value',)


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"item_slug": ("item_name",)}
    form = ItemTaggitForm

    class Media:
        js = [
            'admin/js/jquery.init.js',
            'autocomplete_light/jquery.init.js',
        ]


admin.site.register(Item, ItemAdmin)
admin.site.register(ItemTypes)
