import os
import shutil

from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.functional import cached_property

from core.utils.cache import DonatesCacheList, DonateCache
from django.conf import settings

from core.utils.payment import cash_sender
from group.models.managers import CashSendManager


class Group(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')
    access_token = models.CharField(max_length=200, verbose_name='Токен')
    group_id = models.CharField(max_length=20, db_index=True, unique=True,
                                verbose_name='Идентификатор сообщества в VK')
    min_donate = models.IntegerField(default=0, verbose_name='Величина минимального доната')
    commission = models.IntegerField(default=15, verbose_name='Комиссия')
    admin = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, verbose_name='Админ')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

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
    name = models.CharField(max_length=64, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    amount = models.IntegerField(null=True, blank=True, verbose_name='Сумма')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='targets', verbose_name='Группа')
    active = models.BooleanField(default=False, verbose_name='Статус')
    donates_sum = models.IntegerField(default=0, verbose_name='Накоплено')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Цель'
        verbose_name_plural = 'Цели'

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
    purse_help_text = 'Для Яндекс Деньги: 410011729822xxx <br>' \
                      'Для VISA: 123456789123xxxx 01/01 <br>' \
                      'Для QIWI: +7910123xxxx'
    YD, VISA, QIWI = 45, 94, 63
    CUR = (
        (YD, 'Яндекс Деньги'),
        (VISA, 'VISA'),
        (QIWI, 'QIWI')
    )
    currency = models.IntegerField(choices=CUR, null=True, verbose_name='Валюта перевода')
    purse = models.CharField(max_length=64, blank=True, verbose_name='Реквизиты', help_text=purse_help_text)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, verbose_name='Группа')

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = 'Кошелёк'
        verbose_name_plural = 'Кошельки'


class CashSend(models.Model):
    objects = CashSendManager()
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
    payment_id = models.CharField(max_length=16, db_index=True,
                                  verbose_name='Идентификатор перевода')
    status = models.IntegerField(choices=STATUSES, default=CREATED,
                                 verbose_name='Статус')
    amount = models.IntegerField(verbose_name='Сумма')
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_dt = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    wallet = models.ForeignKey(Wallet, related_name='cash_sends',
                               on_delete=models.CASCADE, verbose_name='Кошелёк')

    class Meta:
        verbose_name = 'Вывод'
        verbose_name_plural = 'Выводы'

    def __str__(self):
        return str(self.id)

    @staticmethod
    def send(wallet, amount):
        if not (wallet.purse and wallet.currency):
            return None
        payment_id = cash_sender.cash_send(wallet, amount)
        if payment_id:
            return CashSend.objects.create(payment_id=payment_id, amount=amount, wallet=wallet)
        return None
