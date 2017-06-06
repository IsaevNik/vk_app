from django.db import models

from group.models import CashSend
from group.models import Target
from group.models.managers import OrderManager


class Donate(models.Model):
    vk_id = models.CharField(max_length=20)
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name='donates')

    def __str__(self):
        return self.vk_id
    
    class Meta:
        verbose_name = 'Донат'
        verbose_name_plural = 'Донаты'


class Order(models.Model):
    objects = OrderManager()
    REGISTERED = 0
    DEPOSITED = 1
    DECLINED = 2
    SEND = 3
    STATUSES = ((REGISTERED, 'Зарегестрирован'),
                (DEPOSITED, 'Одобрен'),
                (DECLINED, 'Отклонён'),
                (SEND, 'Отправлен'))
    amount = models.IntegerField(default=0, verbose_name='Сумма')
    status = models.IntegerField(choices=STATUSES, default=REGISTERED, verbose_name='Статус')
    create_dt = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_dt = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    transaction_id = models.CharField(max_length=100, null=True, blank=True,
                                      verbose_name='Номер транзакции')
    donate = models.OneToOneField(Donate, on_delete=models.CASCADE, verbose_name='Донат')
    cur_id = models.IntegerField(null=True, verbose_name='Вид платежа')
    cash_send = models.ForeignKey(CashSend, on_delete=models.SET_NULL,
                                  null=True, related_name='orders')

    def __str__(self):
        return str(self.id)

    @classmethod
    def set_to_sended(cls, ids, cash_send):
        Order.objects.filter(id__in=ids).update(cash_send=cash_send)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'

