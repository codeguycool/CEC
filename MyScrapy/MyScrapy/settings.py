# -*- coding: utf-8 -*-


#######################
# Custom settings(DB)
#######################

from Entertainment_Data_Provider.settings import (
    LMDB_DB_NAME, LMDB_DB_HOST, LMDB_DB_PORT, LMDB_DB_ACCOUNT,
    LSDB_DB_NAME, LSDB_DB_HOST, LSDB_DB_PORT, LSDB_DB_ACCOUNT,
    LADB_DB_NAME, LADB_DB_HOST, LADB_DB_PORT, LADB_DB_ACCOUNT)


#######################
# Custom settings(DIR)
#######################

from Entertainment_Data_Provider.settings import DIR_TEMP, DIR_LOG
DIR_SCRAPY_LOG = '%s/scrapy' % DIR_LOG
DIR_SCRAPY_CACHE = '%s/scrapy' % DIR_TEMP


# Scrapy settings for MyScrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
# http://scrapy.readthedocs.io/en/latest/topics/settings.html


#######################
# Spider
#######################

BOT_NAME = 'MyScrapy'
SPIDER_MODULES = ['MyScrapy.spiders']
NEWSPIDER_MODULE = 'MyScrapy.spiders'


#############################################################################################################
# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#############################################################################################################

# SPIDER_MIDDLEWARES = {
#    'MyScrapy.middlewares.cache.ItemCacheMiddleware': 1000,
# }


#############################################################################################################
# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#############################################################################################################

DOWNLOADER_MIDDLEWARES = {
    # Engine side
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,  # disable scrapy UserAgent middleware
    'MyScrapy.middlewares.useragent.RotateUserAgentMiddleware': 400,  # enable MyScrapy Rotate UserAgent middleware
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 550,
    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,  # need set COOKIES_ENABLED
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.chunked.ChunkedTransferMiddleware': 830,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,  # need set HTTPCACHE_ENABLED
    # Downloader side
}


#############################################################################################################
# Enable and configure cookies
# See http://scrapy.readthedocs.io/en/latest/topics/downloader-middleware.html#module-scrapy.downloadermiddlewares.cookies
#############################################################################################################

COOKIES_ENABLED = False  # Disable cookies as some sites may use cookies to spot bot behaviour
COOKIES_DEBUG = False  # If enabled, Scrapy will log all cookies sent in requests  and all cookies received in responses


#############################################################################################################
# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#############################################################################################################

HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = '%s/httpcache' % DIR_TEMP
HTTPCACHE_IGNORE_MISSING = False
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_IGNORE_SCHEMES = ['file']
HTTPCACHE_DBM_MODULE = 'anydbm'
HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.RFC2616Policy'
HTTPCACHE_GZIP = False


#############################################################################################################
# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#############################################################################################################

EXTENSIONS = {
    'scrapy.extensions.debug.StackTraceDump': 0,
    'MyScrapy.extensions.logger.SpiderLogger': 0,
    'MyScrapy.extensions.torproxy.TorProxy': 0,
}


#############################################################################################################
# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#############################################################################################################

AUTOTHROTTLE_ENABLED = True
# AUTOTHROTTLE_START_DELAY=5  # The initial download delay
# AUTOTHROTTLE_MAX_DELAY=60  # The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_DEBUG=False  # Enable showing throttling stats for every response received:


#############################################################################################################
# Configure the Close spider extension
# See http://scrapy.readthedocs.io/en/latest/topics/extensions.html#module-scrapy.extensions.closespider
#############################################################################################################

CLOSESPIDER_TIMEOUT = 0
CLOSESPIDER_PAGECOUNT = 0
CLOSESPIDER_ITEMCOUNT = 0
CLOSESPIDER_ERRORCOUNT = 0


#############################################################################################################
# Configure Tor Proxy
#############################################################################################################

PROXY_ENABLED = True
PROXY_URI = 'http://localhost:8123'  # tor proxy


#######################################
# Override the default request headers:
#######################################

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}


#######################################
# Concurrent Request
#######################################

CONCURRENT_ITEMS = 100
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 0


#######################################
# Download
#######################################

DOWNLOAD_DELAY = 2
DOWNLOAD_TIMEOUT = 60

#######################################
# Log
#######################################

LOG_ENABLED = True
LOG_ENCODING = 'utf-8'
LOG_FORMATTER = 'scrapy.logformatter.LogFormatter'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_STDOUT = False
LOG_LEVEL = 'DEBUG'
LOG_FILE = None
LOG_UNSERIALIZABLE_REQUESTS = False


#######################################
# Mail
#######################################

MAIL_HOST = 'localhost'
MAIL_PORT = 25
MAIL_FROM = 'scrapy@localhost'
MAIL_USER = None
MAIL_PASS = None


#######################################
# Retry
#######################################

RETRY_ENABLED = True
RETRY_TIMES = 2  # initial response + 2 retries = 3 requests
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 408]
RETRY_PRIORITY_ADJUST = -1


#######################################
# other
#######################################

ROBOTSTXT_OBEY = True
