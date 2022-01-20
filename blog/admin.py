from django.contrib import admin
from django.forms import ModelForm

# Register your models here.
from .models import BlogPost, EmailOrder


class BlogPostAdminForm(ModelForm):
    model = BlogPost

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({'style': 'font-family: monospace, monospace;'})


class BlogPostAdmin(admin.ModelAdmin):
    model = BlogPost
    form = BlogPostAdminForm
    prepopulated_fields = {'slug_title': ('title',)}


class EmailOrderAdmin(admin.ModelAdmin):
    model = EmailOrder


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(EmailOrder, EmailOrderAdmin)