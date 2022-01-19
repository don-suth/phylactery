from django.contrib import admin

# Register your models here.
from .models import BlogPost, EmailOrder


class BlogPostAdmin(admin.ModelAdmin):
    model = BlogPost
    prepopulated_fields = {'slug_title': ('title',)}


class EmailOrderAdmin(admin.ModelAdmin):
    model = EmailOrder


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(EmailOrder, EmailOrderAdmin)