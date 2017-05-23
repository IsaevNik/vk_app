from django_redis import get_redis_connection

redis_client = get_redis_connection()


class BaseCacheList:

    limit = 3

    @property
    def key(self):
        raise NotImplementedError

    def add(self, val):
        redis_client.lpush(self.key, val)

    def all(self):
        return [item.decode('utf-8') for item in redis_client.lrange(self.key, 0, -1)]

    def __len__(self):
        return redis_client.llen(self.key)

    def rpop(self):
        return redis_client.rpop(self.key).decode('utf-8')

    def __iter__(self):
        return self.all().__iter__()

    class Meta:
        abstract = True


class DonatesListCacheList(BaseCacheList):
    key = 'donate_ids'


class DonatesCache:
    """
    """
    key = 'donate'
    sep = ':'

    def create(self, num, text, avatar, user_data):
        if len(donates_list) == donates_list.limit:
            num = donates_list.rpop()
            self.delete(num)
        data = {
            'text': text,
            'avatar': avatar,
            'last_name': user_data.get('last_name'),
            'first_name': user_data.get('first_name')
        }
        redis_client.hmset(self._full_key(num), data)
        donates_list.add(num)

    def _full_key(self, num):
        return self.sep.join([self.key, str(num)])

    def get_all(self, num):
        return {k.decode('utf-8'): v.decode('utf-8')
                for k, v in redis_client.hgetall(self._full_key(num)).items()}

    def delete(self, num):
        redis_client.delete(self._full_key(num))


donates_list = DonatesListCacheList()
donates = DonatesCache()
