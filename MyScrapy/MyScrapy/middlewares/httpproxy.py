# -*- coding: utf-8 -*-

# std
from six.moves.urllib.request import getproxies, proxy_bypass

# 3rd
from scrapy.conf import settings
from scrapy.utils.httpobj import urlparse_cached

# project
from lib.proxyscraper import FreeProxyScraper


class FreeProxyMiddleware(object):
    """ 使用網路上提供的免費proxy

    透過 ProxyScrapyer 定時去要新的 proxy list
    """

    def __init__(self):
        self.proxy_scraper = FreeProxyScraper()

    def process_request(self, request, spider):
        # ignore if proxy is already set
        if 'proxy' in request.meta:
            return

        parsed = urlparse_cached(request)
        scheme = parsed.scheme

        # 'no_proxy' is only supported by http schemes
        if scheme in ('http', 'https') and proxy_bypass(parsed.hostname):
            return

        proxy = self.proxy_scraper.proxy
        self.proxy_scraper.remove(proxy)

        request.meta['proxy'] = proxy['url']


class TorProxyMiddleware(object):
    """  使用 tor 做為 proxy
    """

    def process_request(self, request, spider):
        request.meta['proxy'] = settings.get('HTTP_PROXY')
