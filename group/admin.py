from django.contrib import admin
from django.db.models import Sum
from django.contrib import messages

from group.models import Group, Target, Order, Donate, CashSend, Wallet
from core.utils.tasks import check_cash_send
# Register your models here.


class GroupAdmin(admin.ModelAdmin):
    actions = ['send_cash']
    list_display = ('__str__', 'donates', 'donates_with_profit', 'commission')

    def donates(self, obj):
        result = Order.objects.filter(donate__target__group=obj,
                                      status=Order.DEPOSITED).aggregate(Sum('amount'))
        return result.get('amount__sum')

    donates.short_description = 'Активных донатов на сумму'

    def donates_with_profit(self, obj):
        amount_sum = self.donates(obj)
        return int(amount_sum * (1 - obj.commission / 100.0))
    donates_with_profit.short_description = 'Активных на сумму с учётом комиссии'

    def send_cash(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, 'Можно выбрать только одну группу')
        obj = queryset[0]
        orders_id = list(Order.objects.filter(donate__target__group=obj,
                                              status=Order.DEPOSITED).values('id'))
        amount = self.donates_with_profit(obj)
        if amount > 1000:
            cash_send = CashSend.send(obj.wallet, amount)
            if cash_send:
                Order.set_to_sended(orders_id, cash_send)
                messages.success(request, 'Перевод поступил в обработку')
                check_cash_send.apply_async((cash_send.id,), countdown=2*60*60)
            else:
                messages.error(request, 'Отправка не удалась, смотри логи')
        else:
            messages.error(request, 'Сумма должна быть больше 1000 рублей')
    send_cash.description = 'Отправить'


admin.site.register(Group, GroupAdmin)
admin.site.register(Target)
admin.site.register(Order)
admin.site.register(Donate)
admin.site.register(Wallet)
