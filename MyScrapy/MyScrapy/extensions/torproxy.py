# -*- coding: utf-8 -*-

# std
import os

# 3rd
from scrapy import signals
from scrapy.exceptions import NotConfigured


class TorProxy(object):

    def __init__(self, crawler):
        self.proxy_uri = crawler.settings.get('PROXY_URI')

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.get('PROXY_ENABLED'):
            raise NotConfigured

        obj = cls(crawler)
        crawler.signals.connect(obj.setup_proxy, signal=signals.spider_opened)
        return obj

    def setup_proxy(self, spider):
        os.environ['http_proxy'] = self.proxy_uri
        os.environ['https_proxy'] = self.proxy_uri
