import random
import string
from django.conf import settings
import redis


class RedisBackend(object):
    def __init__(self):
        self.redis_server = redis.StrictRedis()

    def flush_db(self):
        self.redis_server.flushdb()

    def load_endpoints(self, prefix):
        endpoints = []
        for k in self.redis_server.keys(prefix + '*'):
            v = self.redis_server.get(k)
            endpoints.append(v.decode('utf-8'))
        return endpoints

    def save_endpoint(self, name, endpoint):
        random_suffix = ''.join(
            [random.choice(string.digits + string.ascii_letters) for x in range(16)]
        )
        id = '{name}#{suffix}'.format(name=name, suffix=random_suffix)
        self.redis_server.set(id, endpoint)
        self.redis_server.expire(id, settings.ENDPOINT_ENTRY_TIMEOUT)
