# -*-coding: utf-8 -*-
""" Redis Cache tools.
"""

# std
import json

# 3rd party library
import redis

# app module
from framework.py_utilities import Singleton
from framework.sys_const import LOG_NOTICE
from framework.sys_tools import log
from framework.sys_var import CACHE_EXPIRE_TIME, CACHE_DB_NUM, SOCKET_FILE


class DBSingleton(Singleton):
    """ Metaclass for each cache database.
    """
    def __call__(cls, *args, **kwargs):
        key = 'DBSingleton-%s' % kwargs['db'] 

        if key not in cls._instances:
            cls._instances[key] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]


class RedisPool(redis.ConnectionPool):
    """ Redis connection pool.
    Default number of connection is 2 ** 31.
    """
    __metaclass__ = DBSingleton

    def __init__(self, socket_file=SOCKET_FILE, db=CACHE_DB_NUM, **kargs):
        super(RedisPool, self).__init__(
            connection_class=redis.UnixDomainSocketConnection, path=socket_file, db=db, **kargs
        )


class Cache(redis.StrictRedis):
    """ Redis connection.
    """
    def __init__(self, db=CACHE_DB_NUM, **kargs):
        super(Cache, self).__init__(connection_pool=RedisPool(db=db), **kargs)

    def get_by_request(self, request):
        """ Get cache data with request information.

        [Arguments]
            request : request object of cherrypy.

        [Return]
            value   : dict.
                API response data.
        """
        key = get_api_key(request)

        value = err_not_raise(self.get, key)
        if value:
            return json.loads(value)
        return value

    def set_by_request(self, request, value):
        """ Cache response data with cache key which get from request information.

        [Arguments]
            request : request object of cherrypy.

            value   : dict.
                API response data.
        """
        key = get_api_key(request)
        err_not_raise(self.setex, name=key, time=CACHE_EXPIRE_TIME, value=json.dumps(value))


def get_api_key(request):
    """ Get cache key from request information.

    [Arguments]
        request : request object of cherrypy.
    """
    # reuqest url as key
    if request.query_string:
        return '%s?%s' % (request.path_info, request.query_string)  # e.g. "/movies?type=latest&lang=TCH"
    return request.path_info  # e.g. "/movies"


def err_not_raise(method, *args, **kargs):
    try:
        return method(*args, **kargs)
    except Exception, e:
        log.send(LOG_NOTICE, 'Cache Exception: %s' % str(e))
        return None


def cache_request(method):
    """ cache decorator for resource standard input object.
    REMOVEME: If this is no use.
    """
    def wrapper(self, url, params, request, response):
        cache = Cache()

        key = get_api_key(request)
        value = err_not_raise(cache.get, key)
        if value:
            return json.loads(value)

        ret = method(self, url, params, request, response)

        err_not_raise(self.setex, name=key, time=CACHE_EXPIRE_TIME, value=json.dumps(ret))

        return ret
    return wrapper
