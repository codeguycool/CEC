# -*- coding: utf-8 -*-

""" 好熱迪(新歌、排行)的網路爬蟲

"""

# 3rd
import scrapy

# project
from MyScrapy.items.ktv import KtvItem
from MyScrapy.pipelines.ktv import cleardb


class HolidaySpider(scrapy.Spider):
    name = 'holiday'
    allowed_domains = ['holiday.com.tw', 'youtube.com']
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.ktv.KtvPipeline': 300},
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_TIMEOUT': 90,
    }

    def start_requests(self):
        cleardb()

        # 新歌
        yield scrapy.Request('http://www.holiday.com.tw/song/NewSong.aspx?kind=c',
                             callback=self.parse_list, meta={'type': 'M1'})
        yield scrapy.Request('http://www.holiday.com.tw/song/NewSong.aspx?kind=t',
                             callback=self.parse_list, meta={'type': 'T1'})
        yield scrapy.Request('http://www.holiday.com.tw/song/NewSong.aspx?kind=g',
                             callback=self.parse_list, meta={'type': 'C1'})
        yield scrapy.Request('http://www.holiday.com.tw/song/NewSong.aspx?kind=w',
                             callback=self.parse_list, meta={'type': 'E1'})
        yield scrapy.Request('http://www.holiday.com.tw/song/NewSong.aspx?kind=j',
                             callback=self.parse_list, meta={'type': 'J1'})

        # 排行
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=tc',
                             callback=self.parse_list, meta={'type': 'M2'})
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=tt',
                             callback=self.parse_list, meta={'type': 'T2'})
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=ct',
                             callback=self.parse_list, meta={'type': 'C2'})
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=et',
                             callback=self.parse_list, meta={'type': 'E2'})
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=jt',
                             callback=self.parse_list, meta={'type': 'J2'})

        # 新歌排行
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=nc',
                             callback=self.parse_list, meta={'type': 'M3'})
        yield scrapy.Request('http://www.holiday.com.tw/song/Billboard.aspx?kind=nt',
                             callback=self.parse_list, meta={'type': 'T3'})

    def parse_list(self, response):

        song_type = response.meta['type']

        # 新歌和排行的版面不同
        if song_type[1] == '1':
            title_xpath = "./td[3]/text()"
            artit_xpath = "./td[4]/a/text()"
        else:
            title_xpath = "./td[5]/text()"
            artit_xpath = "./td[6]/a/text()"

        i = 0
        for song in response.xpath(
            "//table[@id='ctl00_ContentPlaceHolder1_dgSong']/tr[position() > 1 and position() < last()]"
        ):
            i += 1
            title = song.xpath(title_xpath)[0].extract().strip()
            artist = song.xpath(artit_xpath)[0].extract().strip()
            lang = song_type[0]
            stype = song_type[1]
            rank = i

            item = KtvItem('holiday', stype, lang, title, artist, rank)
            if item['youtube']:
                yield item
