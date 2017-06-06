from django.contrib import admin
from django.db.models import Sum
from django.contrib import messages

from core.utils.cache import settings_cache
from group.models import Group, Target, Order, Donate, CashSend, Wallet
from core.utils.tasks import check_cash_send
# Register your models here.


class GroupAdmin(admin.ModelAdmin):
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


class OrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'amount', 'with_commission', 'transaction_id',
                    'status', 'cash_send', 'create_dt']
    list_per_page = 20

    def get_queryset(self, request):
        return Order.objects.filter(donate__target__group__admin=request.user)

    def with_commission(self, obj):
        return int(obj.amount * (1 - obj.donate.target.group.commission / 100.0))
    with_commission.short_description = 'С учётом комиссии'


class DonateAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'comment', 'amount', 'with_commission', 'status',
                    'cash_send', 'send_status', 'create_dt')
    list_per_page = 20

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if not request.user.is_superuser:
            group = request.user.group
            active_donate_sum = Order.objects.sum_of_active_by_group(group)
            all_donate_sum = Order.objects.sum_of_all_by_group(group)
            extra_context['group'] = group

            extra_context['active_donate_sum'] = active_donate_sum
            extra_context['active_with_commission'] = int(active_donate_sum * (1 - group.commission / 100.0))

            extra_context['all_donate_sum'] = all_donate_sum
            extra_context['all_donate_sum_with_commission'] = int(all_donate_sum * (1 - group.commission / 100.0))
            extra_context['all_donate_count'] = Order.objects.count_of_all_by_group(group)

            extra_context['sended_donate'] = CashSend.objects.sum_by_group(group, [CashSend.COMPLETED])
            extra_context['sending_donate'] = CashSend.objects.sum_by_group(
                group, [CashSend.CREATED, CashSend.IN_PROCESS])
            extra_context['fail_donate'] = CashSend.objects.sum_by_group(group, [CashSend.FAILED])

        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Donate.objects.all()
        return Donate.objects.select_related(
            'order', 'target__group'
        ).filter(target__group__admin=request.user)

    def amount(self, obj):
        return obj.order.amount
    amount.short_description = 'Сумма'

    def with_commission(self, obj):
        return int(obj.order.amount * (1 - obj.target.group.commission / 100.0))
    with_commission.short_description = 'Сумма с учётом комиссии'

    def status(self, obj):
        return obj.order.get_status_display()
    status.short_description = 'Статус'

    def cash_send(self, obj):
        return bool(obj.order.cash_send)
    cash_send.short_description = 'Отправлялся'
    cash_send.boolean = True

    def send_status(self, obj):
        if obj.order.cash_send:
            return obj.order.cash_send.get_status_display()
        return 'Не переводился'
    send_status.short_description = 'Перевод'

    def create_dt(self, obj):
        return obj.order.create_dt
    create_dt.short_description = 'Дата'


class CashSendAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'payment_id', 'status', 'amount')


admin.site.register(CashSend, CashSendAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Target)
admin.site.register(Donate, DonateAdmin)
admin.site.register(Wallet)

