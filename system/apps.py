from django.apps import AppConfig
from django.db import OperationalError
from django.db import ProgrammingError

from core.utils.cache import settings_cache


class SystemConfig(AppConfig):
    name = 'system'

    def ready(self):
        try:
            from system.models import Setting
            for setting in Setting.objects.all():
                settings_cache.set(setting.key, setting.value)
        except (OperationalError, ProgrammingError):
            pass
