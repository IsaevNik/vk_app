import os
import shutil

from django.db import models
from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.functional import cached_property

from core.utils.cache import DonatesCacheList, DonateCache
from django.conf import settings

from core.utils.payment import cash_sender


class Group(models.Model):
    name = models.CharField(max_length=64)
    access_token = models.CharField(max_length=200)
    group_id = models.CharField(max_length=20, db_index=True, unique=True)
    min_donate = models.IntegerField(default=0)
    commission = models.IntegerField(default=15)

    def __str__(self):
        return '{} {}'.format(str(self.id), self.name)

    @cached_property
    def donates_list(self):
        return DonatesCacheList(self.group_id)

    @property
    def group_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.group_id)

    @property
    def avatars_path(self):
        return os.path.join(self.group_path, settings.AVATARS_DIR)

    @property
    def covers_path(self):
        return os.path.join(self.group_path, settings.COVERS_DIR)

    @property
    def relative_path_avatar(self):
        return os.path.join(self.group_id, settings.AVATARS_DIR)

    @property
    def active_target(self):
        return self.targets.filter(active=True).first()


@receiver(post_save, sender=Group)
def create_group(sender, instance, created, **kwargs):
    if created:
        if not os.path.exists(instance.avatars_path):
            os.makedirs(instance.avatars_path)

        if not os.path.exists(instance.covers_path):
            os.makedirs(instance.covers_path)

        Target.objects.create(name=instance.name, group=instance, active=True)
        Wallet.objects.create(group=instance)


@receiver(pre_delete, sender=Group)
def delete_group(sender, instance, **kwargs):

    if os.path.exists(instance.group_path):
        shutil.rmtree(instance.group_path)

    for donate_id in instance.donates_list:
        DonateCache.delete(donate_id)

    instance.donates_list.delete()


class Target(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    amount = models.IntegerField(null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='targets')
    active = models.BooleanField(default=False)
    donates_sum = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.active:
            Target.objects.filter(
                group=self.group, active=True
            ).exclude(id=self.id).update(active=False)
        else:
            if Target.objects.filter(
                group=self.group, active=True
            ).exclude(id=self.id).count() != 1:
                first_target = Target.objects.filter(group=self.group).first()
                if first_target:
                    first_target.active = True
                    first_target.save()
        super().save(*args, **kwargs)

    def update_sum(self, amount):
        self.donates_sum += amount
        self.save()


class Wallet(models.Model):
    YD, VISA, QIWI = 45, 94, 63
    CUR = (
        (YD, 'Яндекс Деньги'),
        (VISA, 'VISA'),
        (QIWI, 'QIWI')
    )
    currency = models.IntegerField(choices=CUR, null=True)
    purse = models.CharField(max_length=64, blank=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.group.name


class CashSend(models.Model):
    CREATED, IN_PROCESS, COMPLETED, CANCELED, FAILED = 0, 1, 2, 3, 4
    STATUSES = (
        (CREATED, 'Создан'),
        (IN_PROCESS, 'В процессе'),
        (COMPLETED, 'Выполнен'),
        (CANCELED, 'Отменён'),
        (FAILED, 'Ошибка')
    )
    STATUSES_MAP = {
        'New': CREATED,
        'In process': IN_PROCESS,
        'Completed': COMPLETED,
        'Canceled': CANCELED
    }
    payment_id = models.CharField(max_length=16, db_index=True)
    status = models.IntegerField(choices=STATUSES, default=CREATED)
    amount = models.IntegerField()
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)
    wallet = models.ForeignKey(Wallet, related_name='cash_sends',
                               on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

    @staticmethod
    def send(wallet, amount):
        if not (wallet.purse or wallet.currency):
            return None
        payment_id = cash_sender.cash_send(wallet, amount)
        if payment_id:
            return CashSend.objects.create(payment_id=payment_id, amount=amount, wallet=wallet)
        return None
