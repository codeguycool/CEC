# -*- coding: utf-8 -*-

# std
import json
import os
import re
import urlparse

# project
from MyScrapy.items.tv import TvItem
from MyScrapy.lib.extractor import XpathExtractor, ValueExtract
from MyScrapy.lib.flvextractor import FlvExtractor
from MyScrapy.lib.htmlcache import HtmlCache
from MyScrapy.lib.ydextractor import YDExtractor
from MyScrapy.parsers import WebParser


class KuboTvParser(WebParser):

    def _get_htmlcache(self):
        return HtmlCache(self.url, self._get_urlid(), expiredays=1)

    def _get_urlid(self):
        pageid = os.path.splitext(self.url)[0].split('-')[-1]
        if not re.match('\d', pageid):
            raise ValueError('id is not number')
        return pageid

    def _get_extractors(self):
        return [
            XpathExtractor(
                'title', self.html,
                "//div[@class='vshow']/h2/text()"
            ),
            XpathExtractor(
                'akas', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '別名:')])",
                postback=self.split_akas
            ),
            XpathExtractor(
                'posterurl', self.html,
                "//div[@class='vpic']/img/@src"
            ),
            XpathExtractor(
                'stars', self.html,
                u"//div[@class='vshow']/p[contains(text(), '演出：')]/a/text()",
                islist=True
            ),
            XpathExtractor(
                'genres', self.html,
                u"//div[@class='vshow']/p[contains(text(), '類型：')]/a/text()",
                islist=True
            ),
            XpathExtractor(
                'kind', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '分類：')])",
                postback=self.get_kind
            ),
            XpathExtractor(
                'region', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '分類：')])",
                postback=self.get_region
            ),
            XpathExtractor(
                'year', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '分類：')])",
                postback=self.get_year
            ),
            XpathExtractor(
                'completed', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '分類：')])",
                postback=self.get_completed_flag
            ),
            XpathExtractor(
                'update_eps', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '分類：')])",
                postback=self.get_update_ep
            ),
            XpathExtractor(
                'total_eps', self.html,
                u"string(//div[@class='vshow']/p[contains(text(), '分類：')])",
                postback=self.get_total_eps
            ),
            XpathExtractor(
                'description', self.html,
                "string(//div[@class='vcs']/ul)"
            ),
            XpathExtractor(
                'rdate', self.html,
                u"string(//text()[contains(., '更新時間：')])",
                postback=self.get_rdate
            ),
            ValueExtract('source', 'kubo'),
            ValueExtract('id', self.get_id()),
            ValueExtract('dbid', None),
            ValueExtract('url', self.url),
            ValueExtract('play_urls', {}, postback=self.get_play_urls),
        ]

    def _get_item(self):
        return TvItem()

    def split_akas(self, akas):
        if isinstance(akas, basestring):
            akas = akas[3:].split('/')  # 例: akas = '又名:XXXX'
            akas = akas if akas != [u''] else []
        else:
            raise Exception("akas isn't string")
        return akas

    def get_tokens(self, rawtext):
        """

        :param rawtext:  分類：台灣劇 | 地區：台灣 | 年份：2015 | 分級：普通級 | 連載：158
        :return:
        """
        tokens = rawtext.split(u'|')
        tokens = [token.strip() for token in tokens]  # ["分類：台灣劇", "地區：台灣"]
        token_dict = {}
        for token in tokens:
            k, v = token.split(u'：')
            token_dict[k] = v  # {"分類": "台灣劇", "地區": "台灣"}
        return token_dict

    def get_kind(self, rawtext):
        tokens = self.get_tokens(rawtext)
        kind = tokens.get(u'分類', None)
        if kind is None:
            raise ValueError("kind can't be None")

        kind_number = {
            u'動漫': 0,
            u'台灣劇': 1,
            u'韓劇': 2,
            u'日劇': 3,
            u'大陸劇': 4,
            u'港劇': 5,
            u'歐美劇': 6,
            u'新/馬/泰/其他劇': 7,
            u'布袋戲': 8
        }.get(kind, None)

        if kind_number is None:
            raise Exception("can't find match kind(%s), %s" % (kind, self.url))
        return kind_number

    def get_region(self, rawtext):
        tokens = self.get_tokens(rawtext)
        region = tokens.get(u'地區', None)
        return region if region != '' else None

    def get_year(self, rawtext):
        tokens = self.get_tokens(rawtext)
        year = tokens.get(u'年份', None)
        return year if year != '' else None

    def get_completed_flag(self, rawtext):
        tokens = self.get_tokens(rawtext)
        result = re.search(u'([^\(]*)(?=\(估計共(\d*)集\))?', tokens.get(u'連載'))
        if result is not None:
            return True if result.group(1) == u'完結' else False
        return None

    def get_update_ep(self, rawtext):
        tokens = self.get_tokens(rawtext)
        result = re.search(u'([^\(]*)(?=\(估計共(\d*)集\))?', tokens.get(u'連載'))
        if result is not None:
            return result.group(1) if self.item['completed'] is False and result.group(1) != '' else None
        return None

    def get_total_eps(self, rawtext):
        tokens = self.get_tokens(rawtext)
        result = re.search(u'([^\(]*)(?=\(估計共(\d*)集\))?', tokens.get(u'連載'))
        if result is not None:
            return result.group(2) if result.group(2) != '' else None
        return None

    def get_rdate(self, rdate):
        return rdate.replace('|', '').strip()[5:]

    def get_id(self):
        return 'kb_%s' % self._get_urlid()

    def get_play_urls(self, play_urls):

        # youtube and dailymotion
        yd_play_urls = self.selector.xpath("//a[contains(@href, 'youtube.php?')]/@href").extract()
        yd_extractor = YDExtractor()
        yd_resources = yd_extractor.get_video_resources(yd_play_urls)

        # other flvs
        flv_play_urls = self.selector.xpath(
            "//div[contains(@id, 'FLV')]//a[contains(@href, 'vod-play-id-')]/@href"
        ).extract()
        flv_play_urls = [urlparse.urljoin(self.url, url) for url in flv_play_urls]
        flv_extractor = FlvExtractor()
        flv_resources = flv_extractor.get_video_resources(flv_play_urls)
        flv_resources.update(yd_resources)
        return json.dumps(flv_resources, ensure_ascii=False)
