import os
import shutil

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.functional import cached_property

from core.utils.cache import DonatesCacheList, Donate
from django.conf import settings


class Group(models.Model):
    name = models.CharField(max_length=64)
    access_token = models.CharField(max_length=200)
    group_id = models.CharField(max_length=20, db_index=True, unique=True)

    def __str__(self):
        return '{} {}'.format(str(self.id), self.name)

    @cached_property
    def donates_list(self):
        return DonatesCacheList(self.group_id)

    @property
    def groups_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.group_id)

    @property
    def avatars_path(self):
        return os.path.join(self.groups_path, settings.AVATARS_DIR)

    @property
    def covers_path(self):
        return os.path.join(self.groups_path, settings.COVERS_DIR)


@receiver(post_save, sender=Group)
def create_group(sender, instance, created, **kwargs):
    if created:
        if not os.path.exists(instance.avatars_path):
            os.makedirs(instance.avatars_path)

        if not os.path.exists(instance.covers_path):
            os.makedirs(instance.covers_path)


@receiver(pre_delete, sender=Group)
def delete_group(sender, instance, **kwargs):

    if os.path.exists(instance.group_path):
        shutil.rmtree(instance.group_path)

    for donate_id in instance.donates_list:
        Donate.delete(donate_id)

    instance.donates_list.delete()

