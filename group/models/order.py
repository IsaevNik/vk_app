from django.db import models

from group.models import Target


class Donate(models.Model):
    vk_id = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name='donates')

    def __str__(self):
        return str(self.id)


class Order(models.Model):
    REGISTERED = 0
    DEPOSITED = 1
    DECLINED = 2
    STATUSES = ((REGISTERED, 'Зарегестрирован'),
                (DEPOSITED, 'Одобрен'),
                (DECLINED, 'Отклонён'))
    amount = models.IntegerField(default=0)
    status = models.IntegerField(choices=STATUSES, default=REGISTERED)
    create_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    donate = models.OneToOneField(Donate, on_delete=models.CASCADE)
    cur_id = models.IntegerField(null=True)

    def __str__(self):
        return str(self.id)
