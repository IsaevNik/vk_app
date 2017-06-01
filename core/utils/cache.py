from django_redis import get_redis_connection

redis_client = get_redis_connection()


class BaseCacheList:

    limit = 3

    @property
    def key(self):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    @property
    def sep(self):
        raise NotImplementedError

    def add(self, val):
        redis_client.lpush(self.key, val)

    def all(self):
        return [item.decode('utf-8') for item in redis_client.lrange(self.key, 0, -1)]

    def __len__(self):
        return redis_client.llen(self.key)

    def rpop(self):
        return redis_client.rpop(self.key).decode('utf-8')

    def delete(self):
        redis_client.delete(self.key)

    def __iter__(self):
        return self.all().__iter__()

    class Meta:
        abstract = True


class DonatesCacheList(BaseCacheList):
    name = 'donate_ids'
    sep = ':'
    key = ''

    def __init__(self, group_id):
        self.key = self.sep.join([self.name, str(group_id)])


class DonateCache:
    """
    """
    key = 'donate'
    sep = ':'

    @classmethod
    def create(cls, group, num, text, avatar, amount, user_data):
        if len(group.donates_list) == group.donates_list.limit:
            num = group.donates_list.rpop()
            cls.delete(num)
        data = {
            'text': text,
            'avatar': avatar,
            'amount': amount,
            'last_name': user_data.get('last_name'),
            'first_name': user_data.get('first_name')
        }
        redis_client.hmset(cls._full_key(num), data)
        group.donates_list.add(num)

    @classmethod
    def _full_key(cls, num):
        return cls.sep.join([cls.key, str(num)])

    @classmethod
    def get_data(cls, num):
        return {k.decode('utf-8'): v.decode('utf-8')
                for k, v in redis_client.hgetall(cls._full_key(num)).items()}

    @classmethod
    def delete(cls, num):
        redis_client.delete(cls._full_key(num))


class BaseHashCache:
    """
    Базовый класс для хранения хэшей в кэше
    """

    @property
    def key(self):
        raise NotImplementedError

    def get(self, field, *args, **kwargs):
        """
        Получение настройки из кэша
        :param field:       имя настройки
        :return:
        """
        value = redis_client.hget(self.key, field)
        if value:
            return value.decode('utf-8')
        return None

    def set(self, field, value):
        """
        Установка настройки
        :param field:       имя настройки
        :param value:       значение настройки
        :return:
        """
        redis_client.hset(self.key, str(field), value)

    def delete(self, field):
        """
        Удаление настройки
        :param field:       имя настройки
        :return:
        """
        redis_client.hdel(self.key, field)

    class Meta:
        abstract = True


class UUIDGroup(BaseHashCache):

    key = 'uuid_group'

uuid_group = UUIDGroup()


class SettingsCache(BaseHashCache):

    key = 'settings'

    def get(self, field, *args, to_type=None, **kwargs):
        value = super().get(field, *args, **kwargs)
        if value and to_type:
            return to_type(value)
        return value

settings_cache = SettingsCache()
