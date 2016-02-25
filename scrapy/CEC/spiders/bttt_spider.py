# -*- coding: utf-8 -*-

""" bt天堂的網路爬蟲

"""

# std lib
import os
import urlparse
import sys

# 3rd lib
import scrapy
from scrapy.selector import Selector

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj lib
import CEC.items.bttt
import CEC.settings
from CEC.spiders import savecache, is_page_exist, is_page_expire, get_body


class BtTTSpider(scrapy.Spider):
    name = 'bttt'
    allowed_domains = ['www.bttiantang.com']
    start_urls = ['http://www.bttiantang.com/?PageNo=1']
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.bttt_pipeline.BtTTPipeline': 300},
    }

    # step 1, 找出前20頁
    def parse(self, response):
        lastpage = 20
        for page in xrange(1, lastpage + 1):
            url = 'http://www.bttiantang.com/?PageNo=%d' % page
            yield scrapy.Request(url, callback=self.parse_movielist, dont_filter=True)

    # step 2, 找出該分頁中所有電影
    def parse_movielist(self, response):
        movies = response.xpath("//div[@class='item cl']")
        for movie in movies:
            try:
                url = movie.xpath("./div[@class='litpic']/a/@href")[0].extract().strip()
                url = urlparse.urljoin(response.url, url)
                vid = os.path.basename(url).split('.')[0]
                udate = movie.xpath("./div[@class='title']/p[@class='tt cl']/span//text()")[0].extract().strip()

                if is_page_exist(self.name, vid) and not is_page_expire(self.name, vid):
                    yield self.parse_movie(vid, url, udate)
                else:
                    yield scrapy.Request(url, meta={'udate': udate}, callback=self.cache_page)
            except IndexError:
                continue

    # step 3, 暫存頁面
    def cache_page(self, response):
        vid = os.path.basename(response.url).split('.')[0]
        if response.status == 200:
            savecache(self.name, vid, response.body)
            yield self.parse_movie(vid, response.url, response.meta['udate'])

    # step 4, 取得電影資訊
    def parse_movie(self, vid, url, udate):
        item = CEC.items.bttt.BtTTItem()
        item['id'] = vid
        item['info_url'] = url
        item['udate'] = udate

        body = get_body(self.name, item['id'])
        sel = Selector(text=body)

        try:
            item['title'] = sel.xpath("//div[@class='moviedteail_tt']/h1/text()")[0].extract().strip()
        except IndexError:
            item['title'] = None

        try:
            item['imdbid'] \
                = sel.xpath("//ul[@class='moviedteail_list']/li[text()='imdb:']/a/text()")[0].extract().strip()
        except IndexError:
            item['imdbid'] = None

        try:
            item['content_urls'] = sel.xpath("//div[@class='tinfo']/a")
            item['content_urls'] = {
                'torrent_%d' % (index + 1): {
                    'title': item['content_urls'][index].xpath('./@title')[0].extract().strip(),
                    'url': urlparse.urljoin(url, item['content_urls'][index].xpath('./@href')[0].extract().strip())
                }
                for index in xrange(len(item['content_urls']))
            }
        except IndexError:
            item['content_urls'] = {}

        return item


if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(BtTTSpider)
    process.start()