from django.contrib import admin

from group.models import Group, Target, Order, Donate
# Register your models here.

admin.site.register(Group)
admin.site.register(Target)
admin.site.register(Order)
admin.site.register(Donate)
