import os
from flask_caching import Cache

cache = Cache(config={
    #'CACHE_TYPE': 'SimpleCache',
    # "CACHE_DEFAULT_TIMEOUT": 100000
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': os.environ['CACHE_REDIS_HOST'],
    'CACHE_REDIS_PORT': os.environ['CACHE_REDIS_PORT'],
    'CACHE_REDIS_DB': os.environ['CACHE_REDIS_DB'],
    'CACHE_REDIS_URL': os.environ['CACHE_REDIS_URL'],
    'CACHE_DEFAULT_TIMEOUT': os.environ['CACHE_DEFAULT_TIMEOUT']})
