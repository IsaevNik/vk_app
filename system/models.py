from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# Create your models here.
from core.utils.cache import settings_cache


class SettingManager(models.Manager):
    def get_setting(self, key, setting_type):
        try:
            return setting_type(self.get(key=key).value)
        except ValueError:
            raise RuntimeError('Invalid type for setting')

    def get_str(self, key):
        return self.get_setting(key=key, setting_type=str)

    def get_int(self, key):
        return self.get_setting(key=key, setting_type=int)

    def get_float(self, key):
        return self.get_setting(key=key, setting_type=float)

    def set(self, key, value):
        try:
            setting = self.get(key=key)
            setting.value = str(value)
            setting.save()
        except self.model.DoesNotExist:
            pass


class Setting(models.Model):
    objects = SettingManager()

    key = models.CharField(primary_key=True, max_length=100, verbose_name='Название')
    value = models.CharField(max_length=100, verbose_name='Значение')

    def __str__(self):
        return str(self.key)

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'


@receiver(post_save, sender=Setting)
def update_value_in_cache(sender, instance, created, **kwargs):
    settings_cache.set(instance.key, instance.value)


@receiver(post_delete, sender=Setting)
def delete_value_in_cache(sender, instance, **kwargs):
    settings_cache.delete(instance.key)