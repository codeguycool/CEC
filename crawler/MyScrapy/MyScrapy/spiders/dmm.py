# -*- coding: utf-8 -*-

""" dmm的網路爬蟲

"""

# 3rd
import scrapy

# project
from MyScrapy.parsers.dmm import DmmParser


class DmmSpider(scrapy.Spider):
    name = 'dmm'
    allowed_domains = ['www.dmm.co.jp']
    # 利用廠商的所有列表為起始點
    start_urls = ['http://www.dmm.co.jp/digital/videoa/-/maker/=/article=keyword/']
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.av.AvPipeline': 300},
    }

    # step1, 找出所有類別
    def parse(self, response):
        for href in response.xpath("//div[@class='d-sect']/ul[@class='d-item d-boxcollist d-4col lh5']/li/a/@href"):
            link = response.urljoin(href.extract())
            yield scrapy.Request(
                link, cookies={"cklg": "ja", "domain": "dmm.co.jp", "path": "/"}, callback=self.parse_makerlist)

    # step2, 找出某類別的所有廠商
    def parse_makerlist(self, response):
        for href in response.xpath(
                "//div[@class='d-item d-box2col']/div[@class='d-unit']/div[@class='d-boxpicdata d-smalltmb']/a/@href"):
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

        # get item
        for href in response.xpath("//ul[@id='list']/li/div/p[@class='tmb']/a/@href"):
            link = response.urljoin(href.extract())
            parser = DmmParser(link, cookies={"cklg": "ja", "domain": "dmm.co.jp", "path": "/"})
            parser.parse()
            if parser.item is None:
                pass
            else:
                yield parser.item
