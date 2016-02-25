# -*-coding: utf-8 -*-
"""System Constant.
"""


# CherryPy log
LOG_LEVEL_STRING = [
    #EMERGENCY
    '[EMERGENCY]',

    #CRITICAL
    '[CRITICAL]',

    #ALERT
    '[ALERT]',

    #ERROR
    '[ERROR]',

    #WARNING
    '[WARNING]',

    #NOTICE
    '[NOTICE]',

    #INFORMATIONAL
    '[INFORMATIONAL]',

    #DEBUG
    '[DEBUG]'
]
LOG_EMERGENCY, LOG_CRITICAL, LOG_ALERT, LOG_ERROR, LOG_WARNING, \
    LOG_NOTICE, LOG_INFORMATIONAL, LOG_DEBUG = xrange(len(LOG_LEVEL_STRING)) # level


# Language 
LANG_ENG = 'ENG' # English
LANG_SCH = 'SCH' # Simple Chinese
LANG_TCH = 'TCH' # Traditional Chinese


# Database
DB_SRC_ATMOVIES = 'atmovies'
DB_SRC_DOUBAN = 'douban'
DB_SRC_IMDB = 'imdb'

