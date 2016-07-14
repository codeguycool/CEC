# -*- coding: utf-8 -*-

# std
import logging
import random
import time

# 3rd
import requests
from scrapy.selector import Selector


class ProxyScraper(object):

    def __init__(self):
        self.proxies = []
        self.blacklist = set()
        self.scrapy()

    @property
    def proxy(self):
        if len(self.proxies) <= 1:
            logging.info('rescape proxy')
            time.sleep(20)
            self.proxies = []
            self.scrapy()
        return random.choice(self.proxies) if len(self.proxies) > 1 else None

    def add(self, schema, url):
        if schema is None or url is None:
            raise Exception('ivalide proxy')
        if url not in self.blacklist:
            self.proxies.append({'schema': schema, 'url': url})

    def remove(self, proxy):
        if proxy is None:
            return
        self.proxies.remove(proxy)
        self.blacklist.add(proxy['url'])

    def scrapy(self):
        raise NotImplementedError


class FreeProxyScraper(ProxyScraper):

    def add_proxies(self, selectorlist):
        for proxy in selectorlist:
            ip = proxy.xpath('./td[1]/text()').extract()[0]
            port = proxy.xpath('./td[2]/text()').extract()[0]
            schema = 'https' if proxy.xpath('./td[7]/text()').extract()[0] == 'yes' else 'http'
            self.add(schema, '%s://%s:%s' % (schema, ip, port))

    def scrapy(self):
        response = requests.get('http://free-proxy-list.net/', timeout=30)
        if response.status_code == 200:
            selector = Selector(text=response.text)
            self.add_proxies(selector.xpath("//table[@id='proxylisttable']/tbody/tr[td[6][text()='yes'] and position() < 100]"))

            if len(self.proxies) <= 2:
                self.add_proxies(selector.xpath(
                    "//table[@id='proxylisttable']/tbody/tr[td[5][text()='anonymous'] and position() < 100]")
                )
