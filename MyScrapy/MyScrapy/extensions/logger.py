# std
import logging
import os

# 3rd
from twisted.python.log import PythonLoggingObserver
from scrapy import signals

# proj
from MyScrapy.settings import DIR_SCRAPY_LOG


class SpiderLogger(object):

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        crawler.signals.connect(obj.setup_logfile, signal=signals.spider_opened)
        return obj

    def setup_logfile(self, spider):
        observer = PythonLoggingObserver('twisted')
        observer.start()
        if not os.path.exists(DIR_SCRAPY_LOG):
            os.makedirs(DIR_SCRAPY_LOG)
        handler = logging.FileHandler('%s/%s.log' % (DIR_SCRAPY_LOG, spider.name), mode='w')
        handler.setLevel('INFO')
        # logger = logging.getLogger(spider.name)
        # logger.addHandler(handler)
        # logger.setLevel(logging.INFO)
        logging.root.addHandler(handler)
        logging.getLogger("requests").setLevel(logging.WARNING)
