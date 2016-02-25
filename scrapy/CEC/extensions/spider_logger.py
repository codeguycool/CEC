# std lib
import logging

# 3rd lib
from twisted.python.log import PythonLoggingObserver
from scrapy import signals

# proj lib
import CEC.settings


class SpiderLogger(object):

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        crawler.signals.connect(obj.setup_logfile, signal=signals.spider_opened)
        return obj

    def setup_logfile(self, spider):
        observer = PythonLoggingObserver('twisted')
        observer.start()
        handler = logging.FileHandler('%s/%s.log' % (CEC.settings.DIR_LOG, spider.name), mode='w')
        handler.setLevel('DEBUG')
        logger = logging.getLogger(spider.name)
        logging.root.addHandler(handler)