# -*- coding: utf-8 -*-

# std
import os

UNDEFINED = '__UNDEFINED'

############
#  global  #
############

# Directory
DIR_EDP = os.path.dirname(os.path.realpath(__file__))
DIR_SCRAPY = '%s/MyScrapy/MyScrapy' % DIR_EDP  # 勿修改
DIR_CRONTAB = '%s/MyCrontab' % DIR_EDP  # 勿修改
DIR_UNITTEST_MYSCRAPY = '%s/test/MyScrapy' % DIR_EDP  # 勿修改
DIR_LOG = '%s/log' % DIR_EDP
DIR_TEMP = '%s/tmp' % DIR_EDP

# Database
DEFAULT_DB_HOST = 'localhost'
DEFAULT_DB_PORT = 5432
DEFAULT_DB_ACCOUNT = 'postgres'
DEFAULT_DB_PASSWORD = 'postgres'

LMDB_DB_NAME = 'lmdb'
LMDB_DB_HOST = DEFAULT_DB_HOST
LMDB_DB_PORT = DEFAULT_DB_PORT
LMDB_DB_ACCOUNT = DEFAULT_DB_ACCOUNT
LMDB_DB_PASSWORd = DEFAULT_DB_PASSWORD

LSDB_DB_NAME = 'lsdb'
LSDB_DB_HOST = DEFAULT_DB_HOST
LSDB_DB_PORT = DEFAULT_DB_PORT
LSDB_DB_ACCOUNT = DEFAULT_DB_ACCOUNT
LSDB_DB_PASSWORd = DEFAULT_DB_PASSWORD

LADB_DB_NAME = 'ladb'
LADB_DB_HOST = DEFAULT_DB_HOST
LADB_DB_PORT = DEFAULT_DB_PORT
LADB_DB_ACCOUNT = DEFAULT_DB_ACCOUNT
LADB_DB_PASSWORd = DEFAULT_DB_PASSWORD

##############
#  MyScrapy  #
##############

# please refer to MyScrapy.settings

##########################
#  MyCrontab-updateimdb  #
##########################

# DB
IMDB_DB_NAME = 'imdb'
IMDB_DB_HOST = 'localhost'
IMDB_DB_PORT = 5432
IMDB_DB_ACCOUNT = 'postgres'
IMDB_DB_PASSWORD = 'postgres'

# Ftp
FTPHOST = 'ftp.fu-berlin.de'
FTPDIR = '/pub/misc/movies/database/'
EXCLUDE_LIST = [
    'biographies.list.gz', 'miscellaneous.list.gz', 'producers.list.gz', 'quotes.list.gz', 'trivia.list.gz',
    'keywords.list.gz', 'production-companies.list.gz', 'soundtracks.list.gz', 'color-info.list.gz',
    'miscellaneous-companies.list.gz', 'technical.list.gz'
]

# bin
POSTGRESQL_BIN_PATH = '/usr/bin/'
USR_LOCAL_BIN_PATH = '/usr/local/bin/'
USR_SBIN_PATH = '/usr/sbin/'

# Notification
SENDER = UNDEFINED  # 手動修改或是從settings_privacy.py覆寫
RECEIVER = UNDEFINED  # 手動修改或是從settings_privacy.py覆寫

# api key
API_KEY_TMDB = UNDEFINED  # 手動修改或是從settings_privacy.py覆寫

# dir
DIR_IMDB_LOG = '%s/crontab' % DIR_LOG
DIR_IMDB_TEMP = '%s/crontab/updateimdb/' % DIR_TEMP
DIR_IMDB_CSV = '%s/csv' % DIR_IMDB_TEMP
DIR_IMDB_LIST = '%s/list' % DIR_IMDB_TEMP

# 從settings_privacy.py覆寫設定值
if os.path.exists('%s/settings_privacy.py' % DIR_EDP):
    from settings_privacy import *

# 檢查未設值的設定
variables = locals()
for key in variables.keys():
    # 不檢查小寫的變數
    if key.islower():
        continue
    # 勿略 UNDEFINED
    if key == 'UNDEFINED':
        continue
    if variables[key] is UNDEFINED:
        raise ValueError('%s is undefined.' % key)
