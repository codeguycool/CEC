# -*- coding: utf-8 -*-

""" 錢櫃(歌單)的網路爬蟲

"""

# 3rd
import scrapy

# project
from MyScrapy.items.ktv import KtvItem


class CashBoxSpider(scrapy.Spider):
    name = 'cashbox'
    allowed_domains = ['cashboxparty.com', 'youtube.com']
    start_urls = ['http://www.cashboxparty.com/mysong/mysong_search_r.asp']
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'ITEM_PIPELINES': {'MyScrapy.pipelines.ktv.KtvPipeline': 300}
    }

    def parse(self, response):
        lastpage = int(response.xpath("//select[@id='Page']/option[last()]/@value")[0].extract())
        for page in xrange(1, lastpage + 1):
            yield scrapy.FormRequest(response.url, callback=self.parse_songs,  formdata={'Page': str(page)})

    def parse_songs(self, response):
        songs = response.xpath("//form[@id='form1']/table[2]/tr[position() > 1]")
        for song in songs:
            lang = song.xpath("./td[2]/text()")[0].extract().strip()
            title = song.xpath("./td[3]/text()")[0].extract().strip()
            artist = song.xpath("./td[4]/text()")[0].extract().strip()

            lang = {
                u'國語': 'M',
                u'台語': 'T',
                u'英語': 'E',
                u'粵語': 'C',
                u'日語': 'J',
                u'韓語': 'K'
            }.get(lang)

            # 只處理國語、台語、英語...等資料
            if lang is None:
                continue

            item = KtvItem('cashbox', None, lang, title, artist, None)
            yield item
