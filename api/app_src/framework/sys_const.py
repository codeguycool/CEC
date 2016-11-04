# -*-coding: utf-8 -*-
"""System Constant.
"""


# CherryPy log
LOG_LEVEL_STRING = [
    ################
    #   API level  #
    ################
    '[EMERGENCY]',
    '[CRITICAL]',
    '[ALERT]',
    '[ERROR]',  # Basic level for any API error occurred.
    ################
    # System level #
    ################
    '[WARNING]',  # Important system error.
    '[NOTICE]',
    '[INFORMATIONAL]',
    '[DEBUG]'
]
LOG_EMERGENCY, LOG_CRITICAL, LOG_ALERT, LOG_ERROR, LOG_WARNING, \
    LOG_NOTICE, LOG_INFORMATIONAL, LOG_DEBUG = xrange(len(LOG_LEVEL_STRING))  # level


# Language 
LANG_ENG = 'ENG'  # English
LANG_SCH = 'SCH'  # Simple Chinese
LANG_TCH = 'TCH'  # Traditional Chinese


# Database
DB_SRC_ATMOVIES = 'atmovies'
DB_SRC_CHINAYES = 'chinayes'
DB_SRC_DOUBAN = 'douban'
DB_SRC_IMDB = 'imdb'
DB_SRC_KUBO = 'kubo'
DB_SRC_DMM = 'dmm'
DB_ID_PRE_ATMOVIES = 'am_'
DB_ID_PRE_CHINAYES = 'cy_'
DB_ID_PRE_DOUBAN = 'db_'
DB_ID_PRE_IMDB = 'im_'
DB_ID_PRE_KUBO = 'kb_'
