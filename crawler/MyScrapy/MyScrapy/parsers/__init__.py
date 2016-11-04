# -*- coding: utf-8 -*-

""" parser處理各個不同網站的內容，將其轉成item
"""

# 3rd
from scrapy.selector import Selector

# project
from MyScrapy.lib.htmlcache import HtmlCache


class WebParser(object):

    def __init__(self, url, *args, **kwargs):
        self.url = url
        self._htmlcache = self._get_htmlcache()
        self.selector = Selector(text=self.html)
        self.extractors = self._get_extractors()
        self.item = self._get_item()

    def _get_htmlcache(self):
        return HtmlCache(self.url, self._get_urlid())

    def _get_urlid(self):
        raise NotImplementedError

    def _get_extractors(self):
        return []

    def _get_item(self):
        return {}

    @property
    def html(self):
        return self._htmlcache.html

    def parse(self):
        if not self.html:
            self.item = {}
            return

        for extractor in self.extractors:
            self.item[extractor.label] = extractor.extract()

