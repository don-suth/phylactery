from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Rank
admin.site.register(Member)
admin.site.register(Membership)
admin.site.register(Rank)