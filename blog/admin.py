from django.contrib import admin
from django.forms import ModelForm

# Register your models here.
from .models import BlogPost, EmailOrder
from members.models import MemberFlag

class BlogPostAdminForm(ModelForm):
    model = BlogPost

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({'style': 'font-family: monospace, monospace;'})


class BlogPostAdmin(admin.ModelAdmin):
    model = BlogPost
    form = BlogPostAdminForm
    prepopulated_fields = {'slug_title': ('title',)}


class MemberFlagsInline(admin.TabularInline):
    model = MemberFlag.emailorders.through
    verbose_name = 'Flag to send emails to'
    verbose_name_plural = 'Flag(s) to send emails to:'
    extra = 1



class EmailOrderAdmin(admin.ModelAdmin):
    model = EmailOrder
    inlines = [MemberFlagsInline]
    exclude = ('flags',)


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(EmailOrder, EmailOrderAdmin)