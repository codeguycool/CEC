# -*- coding: utf-8 -*-

# std
import datetime
import hashlib
import json
import re

# project
from MyScrapy.items.bttt import BtTTItem
from MyScrapy.lib.extractor import XpathExtractor, ValueExtract
from MyScrapy.lib.htmlcache import HtmlCache
from MyScrapy.parsers import WebParser


class BtTTParser(WebParser):

    def __init__(self, url, release_date):
        self.release_date = release_date
        WebParser.__init__(self, url)

    def _get_htmlcache(self):
        return HtmlCache(self.url, self._get_urlid(), expiredays=1)

    def _get_urlid(self):
        # url: http://www.bttt99.com/v/22611/
        result = re.findall("www\.bttt99\.com/v/(\d*)", self.url)
        if result:
            return result[0]
        raise Exception("can't find urlid")

    def _get_extractors(self):
        return [
            XpathExtractor(
                'title', self.html,
                "//div[@class='moviedteail_tt']/h1/text()"
            ),
            XpathExtractor(
                'imdbid', self.html,
                "//ul[@class='moviedteail_list']/li[text()='IMDB:']/a/text()"
            ),
            ValueExtract('id', self._get_urlid()),
            ValueExtract('rdate', self.release_date),
            ValueExtract('info_url', self.url),
            ValueExtract('content_urls', None),
            ValueExtract('md5sum', None, postback=self.calc_md5),
            ValueExtract('udate', None, postback=self.get_udate),
        ]

    def _get_item(self):
        return BtTTItem()

    def calc_md5(self, md5):
        return hashlib.md5(json.dumps(self.item.__dict__, sort_keys=True)).hexdigest()

    def get_udate(self, udate):
        return datetime.datetime.utcnow()
