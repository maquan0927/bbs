import redis, re, json
from django.conf import settings

def analyze_redisurl(redis_url):
    redis_match = re.findall('^redis://(?:|:(.*?)@)([\w\.-]+):(\d+)/(\d+)$', redis_url)
    redis_dict = {
        "host": redis_match[0][1],
        "port": int(redis_match[0][2]),
        "db": int(redis_match[0][3]),
        "password": redis_match[0][0]
    }
    return redis_dict

def get_from_redis(key):
    try:
        r = redis.Redis(**analyze_redisurl(settings.REDIS_URL))
        value = r.get(key)
        if value:
            return json.loads(value)
        return None
    except redis.exceptions.ConnectionError:
        return None


def set_to_redis(key, value, expire=0):
    try:
        r = redis.Redis(**analyze_redisurl(settings.REDIS_URL))
        value = json.dumps(value)
        r.set(key, value, ex=expire)
    except redis.exceptions.ConnectionError:
        return None

def delete_to_redis(key):
    try:
        r = redis.Redis(**analyze_redisurl(redis_url=settings.REDIS_URL))
        r.delete(key)
    except redis.exceptions.ConnectionError:
        return None
