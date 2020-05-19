import redis

import os


pool = redis.ConnectionPool(
    host=os.environ.get('REDIS_HOST'),
    port=os.environ.get('REDIS_PORT'),
    db=1,
    password=os.environ.get('REDIS_PASSWORD')
)
redis_conn = redis.Redis(connection_pool=pool)
