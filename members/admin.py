from django.contrib import admin

# Register your models here.
from .models import Member, Membership, Ranks
admin.site.register(Member)
admin.site.register(Membership)
admin.site.register(Ranks)