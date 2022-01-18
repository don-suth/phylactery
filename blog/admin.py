from django.contrib import admin

# Register your models here.
from .models import BlogPost


class BlogPostAdmin(admin.ModelAdmin):
    model = BlogPost
    prepopulated_fields = {'slug_title': ('title',)}


admin.site.register(BlogPost, BlogPostAdmin)
