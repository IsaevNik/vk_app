from django.contrib import admin
from django.contrib import messages

from core.utils.cache import settings_cache
from group.models import Group, Order, CashSend
from core.utils.tasks import check_cash_send
# Register your models here.


class GroupAdmin(admin.ModelAdmin):
    readonly_fields = ['group_id']
    fields = ['group_id', 'access_token', 'name', 'min_donate']
    actions = ['send_cash']
    list_display = ('__str__', 'donates', 'donates_with_profit', 'commission', 'min_donate')

    def donates(self, obj):
        return Order.objects.sum_of_active_by_group(obj)

    donates.short_description = 'Активных донатов на сумму'

    def donates_with_profit(self, obj):
        amount_sum = self.donates(obj)
        return int(amount_sum * (1 - obj.commission / 100.0))
    donates_with_profit.short_description = 'Активных на сумму с учётом комиссии'

    def send_cash(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, 'Можно выбрать только одну группу')
        obj = queryset[0]
        order_ids = list(Order.objects.filter(donate__target__group=obj,
                                              status=Order.DEPOSITED,
                                              cash_send__isnull=True).values_list('id', flat=True))
        amount = self.donates_with_profit(obj)
        if amount > settings_cache.get('min_send_amount', to_type=int):
            cash_send = CashSend.send(obj.wallet, amount)
            if cash_send:
                Order.objects.filter(id__in=order_ids).update(cash_send=cash_send)
                messages.success(request, 'Перевод поступил в обработку')
                check_cash_send.apply_async((cash_send.id,), countdown=60*60)
            else:
                messages.error(request, 'Отправка не удалась, смотри логи')
        else:
            messages.error(request, 'Сумма должна быть больше 1000 рублей')
    send_cash.description = 'Отправить'

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Group.objects.all()
        return Group.objects.filter(admin=request.user)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if 'send_cash' in actions:
                del actions['send_cash']
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields
        return []














