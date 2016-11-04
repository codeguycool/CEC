# -*-coding: utf-8 -*-
"""System variables.
"""

# std
import os.path

from sys_const import LOG_DEBUG


# API support method
ALLOW_HTTP_METHOD = ['COPY', 'DELETE', 'GET', 'HEAD', 'LINK', 'OPTIONS', 'PATCH', 'POST', 'PURGE', 'PUT', 'UNLINK']

# Database setting
DB_NAME = "lmdb"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
KARAOKE_DB_NAME = "lsdb"
KARAOKE_DB_USER = "postgres"
KARAOKE_DB_PASSWORD = "postgres"
KARAOKE_DB_HOST = "localhost"
KARAOKE_DB_PORT = "5432"
AV_DB_NAME = "ladb"
AV_DB_USER = "postgres"
AV_DB_PASSWORD = "postgres"
AV_DB_HOST = "localhost"
AV_DB_PORT = "5432"
FILE_DB_NAME = "lfdb"
FILE_DB_USER = "postgres"
FILE_DB_PASSWORD = "postgres"
FILE_DB_HOST = "localhost"
FILE_DB_PORT = "5432"

DB_QUERY_TIMEOUT = '50s'

# CherryPy log setting
LOG_LEVEL = LOG_DEBUG  # Default level is DEBUG

# Cache setting
SOCKET_FILE = '/var/run/redis/redis.sock'
CACHE_DB_NUM = 0
CACHE_EXPIRE_TIME = 60*60*3  # Cache data expire time

# reload privacy config
if os.path.exists('%s/privacy_settings.py' % os.path.dirname(__file__)):
    from privacy_settings import *
