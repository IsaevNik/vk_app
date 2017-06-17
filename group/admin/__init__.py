from django.contrib import admin

from group.admin.target import TargetAdmin
from group.admin.wallet import WalletAdmin
from group.admin.donate import DonateAdmin, CashSendAdmin, OrderAdmin
from group.admin.group import GroupAdmin

from group.models import *


admin.site.register(CashSend, CashSendAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Target, TargetAdmin)
admin.site.register(Donate, DonateAdmin)
admin.site.register(Wallet, WalletAdmin)
