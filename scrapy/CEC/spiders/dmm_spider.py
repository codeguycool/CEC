# -*- coding: utf-8 -*-

""" dmm的網路爬蟲

"""

# std lib
import re
import os
import sys

# 3rd lib
import scrapy
from scrapy.selector import Selector

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj lib
import CEC.settings

from CEC.items.dmm_item import Dmmitem
from CEC.spiders import savecache, is_page_exist, is_page_expire, get_body


class DmmSpider(scrapy.Spider):
    name = 'dmm'
    allowed_domains = ['www.dmm.co.jp']
    # maker type url
    start_urls = ['http://www.dmm.co.jp/digital/videoa/-/maker/=/article=keyword/']
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.dmm_pipeline.DmmDbPipeline': 300}
    }

    # step1, 找出所有類別
    def parse(self, response):
        for href in response.xpath("//div[@class='d-sect']/ul[@class='d-item d-boxcollist d-4col lh5']/li/a/@href"):
            link = response.urljoin(href.extract())
            yield scrapy.Request(link, cookies={"cklg": "ja", "domain": "dmm.co.jp", "path": "/"}, callback=self.parse_makerlist)

    # step2, 找出某類別的所有廠商
    def parse_makerlist(self, response):
        for href in response.xpath("//div[@class='d-item d-box2col']/div[@class='d-unit']/div[@class='d-boxpicdata d-smalltmb']/a/@href"):
            link = response.urljoin(href.extract())
            yield scrapy.Request(
                link, cookies={"cklg": "ja", "domain": "dmm.co.jp", "path": "/"}, callback=self.parse_videolist)

    # step3, 找出該廠商所有的影片
    def parse_videolist(self, response):
        # 下一頁
        if response.xpath("//link[@rel='next']/@href"):
            link = response.urljoin(response.xpath("//link[@rel='next']/@href")[0].extract())
            yield scrapy.Request(
                link, cookies={"cklg": "ja", "domain": "dmm.co.jp", "path": "/"}, callback=self.parse_videolist)
        # get detail url
        for href in response.xpath("//ul[@id='list']/li/div/p[@class='tmb']/a/@href"):
            link = response.urljoin(href.extract())
            result = re.search('http://www.dmm.co.jp/.*/cid=(.*)/', link)
            vid = result.group(1) if result is not None and result.group(1) is not None else None

            if is_page_exist(self.name, vid) and not is_page_expire(self.name, vid, 30):
                yield self.parse_video(vid)
            else:
                # 如果沒有暫存檔或是已經過期，執行step4
                yield scrapy.Request(
                    link, cookies={"cklg": "ja", "domain": "dmm.co.jp", "path": "/"}, callback=self.cache_page,
                    meta={'vid': vid})

    # step4, 暫存頁面
    def cache_page(self, response):
        vid = response.meta['vid']

        if response.status == 200:
            savecache(self.name, vid, response.body)
            yield self.parse_video(vid)

    # step5, 取得video資訊
    def parse_video(self, vid):
        body = get_body(self.name, vid)
        sel = Selector(text=body)

        if sel.xpath("//div[@class='page-detail']"):
            item = Dmmitem()
            item['id'] = vid
            item['url'] = "http://www.dmm.co.jp/digital/videoa/-/detail/=/cid=%s/" % vid

            try:
                item['id'] = sel.xpath(u"//table[@class='mg-b20']/tr/td[text()='品番：']/../td[2]/text()").extract()[0]
            except IndexError:
                item['id'] = None

            try:
                item['title'] = sel.xpath("//h1[@id='title']/text()").extract()[0].strip()
            except IndexError:
                item['title'] = None

            try:
                item['posterurl'] = sel.xpath("//div[@id='sample-video']/a/@href").extract()[0].strip()
            except IndexError:
                item['posterurl'] = None

            try:
                item['duration'] = sel.xpath(u"//table[@class='mg-b20']/tr/td[text()='収録時間：']/../td[2]/text()").extract()[0].strip()
                result = re.search('(\d*)', item['duration'])
                if result and result.group(1) is not None:
                    item['duration'] = result.group(1)
            except IndexError:
                item['duration'] = None

            try:
                item['performer'] = sel.xpath("//span[@id='performer']/a/text()").extract()[0]
            except IndexError:
                item['performer'] = None

            try:
                item['category'] = sel.xpath(u"//table[@class='mg-b20']/tr/td[text()='ジャンル：']/../td[2]/a/text()").extract()
            except IndexError:
                item['category'] = []

            try:
                item['rating'] = sel.xpath("//p[@class='d-review__average']/strong/text()").extract()[0].replace(u'点','')
            except IndexError:
                item['rating'] = None

            try:
                item['description'] = sel.xpath("//div[@class='page-detail']/table[@class='mg-b12']/tr/td[1]/div[@class='mg-b20 lh4']/text()").extract()[0].strip()
            except IndexError:
                item['description'] = None

            try:
                item['date'] = sel.xpath(u"//table[@class='mg-b20']/tr/td[text()='商品発売日：']/../td[2]/text()").extract()[0].strip()
                item['date'] = None if item['date'] == '----' else item['date']
            except IndexError:
                item['date'] = None
            try:
                item['samples'] = sel.xpath("//div[@id='sample-image-block']/a[@name='sample-image']/img[@class='mg-b6']/@src").extract()
                for index in range(len(item['samples'])):
                    item['samples'][index] = item['samples'][index].replace('-', 'jp-')
            except IndexError:
                try:
                    item['samples'] = sel.xpath("//div[@id='sample-image-block']/a/img[@class='mg-b6']/@src").extract()
                except IndexError:
                    item['samples'] = []

            try:
                item['maker'] = sel.xpath(u"//table[@class='mg-b20']/tr/td[text()='メーカー：']/../td[2]/a/text()").extract()[0].strip()
            except IndexError:
                item['maker'] = None

            try:
                item['series'] = sel.xpath(u"//table[@class='mg-b20']/tr/td[text()='シリーズ：']/../td[2]/a/text()").extract()[0].strip()
            except IndexError:
                item['series'] = None

            return item

if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(DmmSpider)
    process.start()