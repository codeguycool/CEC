# -*- coding: utf-8 -*-

""" bt天堂的網路爬蟲

"""

# std
import urlparse

# 3rd
import scrapy

# project
from MyScrapy.parsers.bttt import BtTTParser


class BtTTSpider(scrapy.Spider):
    name = 'bttt'
    allowed_domains = ['bttiantang.com']
    start_urls = ['http://www.bttiantang.com']
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.bttt.BtTTPipeline': 300},
        'DOWNLOAD_DELAY': 5,
    }

    def __init__(self, page_limit=None):
        scrapy.Spider.__init__(self)
        self.page_limit = page_limit

        # 更改spider name，以產生獨立的log
        if page_limit:
            self.name = 'bttt-daily'

    # step 1, 爬取指定的分頁
    def parse(self, response):
        # 如果有宣告page_limit, 沒有則抓前20頁
        page_limit = int(self.page_limit) if self.page_limit else 20
        for page in xrange(1, page_limit + 1):
            url = 'http://www.bttiantang.com/?PageNo=%d' % page
            yield scrapy.Request(url, callback=self.parse_movielist, dont_filter=True)

    # step 2, 找出該分頁中所有電影, get item
    def parse_movielist(self, response):
        movies = response.xpath("//div[@class='item cl']")
        for movie in movies:
            try:
                url = movie.xpath("./div[@class='litpic']/a/@href")[0].extract().strip()
                url = urlparse.urljoin(response.url, url)
                release_date = movie.xpath("./div[@class='title']/p[@class='tt cl']/span//text()")[0].extract().strip()

                parser = BtTTParser(url, release_date)
                parser.parse()
                item = parser.item
                if not item or item['title'] is None:
                    continue
                yield item

            except Exception:
                continue
