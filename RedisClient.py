import redis

class RedisClient:
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def exists(self, key):
        return self.client.exists(key)

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

    def sadd(self, key, *values):
        return self.client.sadd(key, *values)

    def smembers(self, key):
        return self.client.smembers(key)

    def delete(self, key):
        return self.client.delete(key)

    def expire(self, key, seconds):
        return self.client.expire(key, seconds)
