# -*- coding: utf-8 -*-

# std
import os

# 3rd
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured


class TorProxyMiddleware(HttpProxyMiddleware):
    """  使用 tor 做為 proxy
    """

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.get('PROXY_ENABLED'):
            raise NotConfigured

        proxy_uri = crawler.settings.get('PROXY_URI')
        os.environ['http_proxy'] = proxy_uri
        os.environ['https_proxy'] = proxy_uri
        return super(TorProxyMiddleware, cls).from_crawler(crawler)
