from django.contrib import admin

from group.models import Order, Donate, CashSend


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

    def get_list_display_links(self, request, list_display):
        if not request.user.is_superuser:
            return None
        else:
            return super().get_list_display_links(request, list_display)


class OrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'amount', 'with_commission', 'transaction_id',
                    'status', 'cash_send', 'create_dt']
    list_per_page = 20

    def get_queryset(self, request):
        return Order.objects.filter(donate__target__group__admin=request.user)

    def with_commission(self, obj):
        return int(obj.amount * (1 - obj.donate.target.group.commission / 100.0))
    with_commission.short_description = 'С учётом комиссии'


class CashSendAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'payment_id', 'status', 'amount')
