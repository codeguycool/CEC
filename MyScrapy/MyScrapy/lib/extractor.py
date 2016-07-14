# -*- coding: utf-8 -*-

# 3rd
from scrapy.selector import Selector


class Extractor(object):

    def __init__(self, label, postback=None):
        self.label = label
        self.postback = postback

    def _process(self):
        pass

    def extract(self):
        value = self._process()
        if self.postback is not None:
            value = self.postback(value)
        return value


class ValueExtract(Extractor):

    def __init__(self, label, value, postback=None):
        Extractor.__init__(self, label, postback)
        self.value = value

    def _process(self):
        return self.value


class XpathExtractor(Extractor):

    def __init__(self, label, html, path, islist=False, postback=None):
        Extractor.__init__(self, label, postback)
        self.html = html
        self.path = path
        self.islist = islist

    def _process(self):
        selector = Selector(text=self.html)
        if self.islist:
            value = selector.xpath(self.path).extract()
        else:
            selectorlist = selector.xpath(self.path)
            if len(selectorlist) > 0:
                value = selectorlist[0].extract().strip()
            else:
                value = None
        return value
