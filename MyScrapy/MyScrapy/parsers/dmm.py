# -*- coding: utf-8 -*-

# std
import datetime
import hashlib
import json
import logging
import re

# 3rd
import requests
from scrapy.selector import Selector

# project
from MyScrapy.items.av import AvItem
from MyScrapy.lib.extractor import XpathExtractor, ValueExtract
from MyScrapy.lib.htmlcache import HtmlCache
from MyScrapy.lib.pathstrategy import SubdirNameBySuffixFilepath, SubdirNameByPrefixFilepath
from MyScrapy.parsers import WebParser


class DmmParser(WebParser):

    def _get_htmlcache(self):
        return HtmlCache(
            self.url, self._get_urlid(),
            old_filepath_inst=SubdirNameBySuffixFilepath(suffix_num=3),
            filepath_inst=SubdirNameByPrefixFilepath(prefix_num=4)
        )

    def _get_urlid(self):
        result = re.search('//www.dmm.co.jp/.*/cid=(.*)/', self.url)
        vid = result.group(1) if result is not None and result.group(1) is not None else None
        if vid is None:
            raise Exception('vid is None')
        return vid

    def _get_extractors(self):
        return [
            XpathExtractor(
                'title', self.html,
                "//h1[@id='title']/text()"
            ),
            XpathExtractor(
                'posterurl', self.html,
                "//div[@id='sample-video']//img/@src",
                postback=self.get_posterurl
            ),
            XpathExtractor(
                'duration', self.html,
                u"//table[@class='mg-b20']/tr/td[text()='収録時間：']/../td[2]/text()",
                postback=self.get_duration
            ),
            XpathExtractor(
                'performer', self.html,
                "//span[@id='performer']/a[contains(@href, '/digital/')]/text()",
                islist=True, postback=self.get_performers
            ),
            XpathExtractor(
                'category', self.html,
                u"//table[@class='mg-b20']/tr/td[text()='ジャンル：']/../td[2]/a/text()",
                islist=True
            ),
            XpathExtractor(
                'rating', self.html,
                "//p[@class='d-review__average']/strong/text()",
                postback=self.get_rating
            ),
            XpathExtractor(
                'description', self.html,
                "//div[@class='page-detail']/table[@class='mg-b12']/tr/td[1]/div[@class='mg-b20 lh4']/text()"
            ),
            XpathExtractor(
                'date', self.html,
                u"//table[@class='mg-b20']/tr/td[text()='商品発売日：']/../td[2]/text()",
                postback=self.get_date
            ),
            XpathExtractor(
                'date2', self.html,
                u"//table[@class='mg-b20']/td[normalize-space(text())='配信開始日：']/following-sibling::td/text()",
                postback=self.get_delivery_date
            ),
            XpathExtractor(
                'samples', self.html,
                "//div[@id='sample-image-block']/a[@name='sample-image']/img[@class='mg-b6']/@src",
                islist=True, postback=self.get_samples
            ),
            XpathExtractor(
                'maker', self.html,
                u"//table[@class='mg-b20']/tr/td[text()='メーカー：']/../td[2]/a/text()"
            ),
            XpathExtractor(
                'series', self.html,
                u"//table[@class='mg-b20']/tr/td[text()='シリーズ：']/../td[2]/a/text()"
            ),
            ValueExtract('id', self._get_urlid()),
            ValueExtract('code', None, postback=self.get_code),
            ValueExtract('url', self.url),
            ValueExtract('md5sum', None, postback=self.get_md5),
            ValueExtract('udate', datetime.datetime.utcnow())
        ]

    def _get_item(self):
        return AvItem()

    def parse(self):
        if self.extractors is not None and self.item is not None:
            for extractor in self.extractors:
                self.item[extractor.label] = extractor.extract()

                # 若title為空，則代表是空白網頁，不繼續處理
                if extractor.label == 'title' and self.item['title'] is None:
                    self.item = None
                    return

    def get_posterurl(self, thumbnailurl):
        if self.selector.xpath("//div[@id='sample-video']/a/@href"):
            return self.selector.xpath("//div[@id='sample-video']/a/@href").extract()[0].strip()
        return thumbnailurl

    def get_duration(self, duration):
        if duration is not None:
            result = re.search('(\d*)', duration)
            if result is not None and result.group(1) != '':
                return result.group(1)

    def get_performers(self, performers):
        result = re.search(".*(?:ajax-performer/=/data=([^']*))", self.html)
        if result:
            ajax_url = 'http://www.dmm.co.jp/digital/videoa/-/detail/ajax-performer/=/data=%s' % result.group(1)
            try:
                response = requests.get(ajax_url, timeout=30)
                if response.status_code == 200:
                    sel = Selector(text=response.content)
                    return sel.xpath("//a/text()").extract()
                else:
                    logging.warning('url: %s, status: %d' % (ajax_url, response.status_code))
            except requests.exceptions.Timeout:
                logging.warning('url: %s timeout' % ajax_url)
        return performers

    def get_rating(self, rating):
        return rating.replace(u'点', '') if rating is not None else None

    def get_date(self, date):
        return None if date == '----' else date

    def get_delivery_date(self, delivery_date):
        delivery_date = delivery_date.split()[0]
        return self.get_date(delivery_date)

    def get_samples(self, samples):
        if samples:
            for index in range(len(samples)):
                samples[index] = samples[index].replace('-', 'jp-')
        elif self.selector.xpath("//div[@id='sample-image-block']/a/img[@class='mg-b6']/@src") is not None:
            samples = self.selector.xpath("//div[@id='sample-image-block']/a/img[@class='mg-b6']/@src").extract()
        return samples

    def get_code(self, vid):
        """ 取番號，如果取不到番號，就用DMM品番

        :param vid:
        :return:
        """
        # example: h_720zex01253
        # 若有_，先把_的部份取完，再取非字母，然後將字母塞進group1, 數字塞進group2
        # (?:[^_]*_) -> _含之前, h_
        # (?:[^a-z]*) -> 非字母, 720
        result = re.search('(?:[^_]*_)?(?:[^a-z]*)([a-z]+)(\d+)', self.item['id'])
        if result:
            tag = result.group(1)
            number = int(result.group(2))
            nubmer = str(number).zfill(3)
            return '%s-%s' % (tag, nubmer)

    def get_md5(self, md5):
        return hashlib.md5(json.dumps(self.item.__dict__, sort_keys=True)).hexdigest()
