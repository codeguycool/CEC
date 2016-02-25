# -*- coding: utf-8 -*-

import scrapy


class Dmmitem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    posterurl = scrapy.Field()
    duration = scrapy.Field()
    # 出演唱
    performer = scrapy.Field()
    category = scrapy.Field()
    rating = scrapy.Field()
    # 廠商
    maker = scrapy.Field()
    # 系列
    series = scrapy.Field()
    # 發片日期
    date = scrapy.Field()
    description = scrapy.Field()
    # 截圖
    samples = scrapy.Field()
    url = scrapy.Field()
    md5sum = scrapy.Field()
    udate = scrapy.Field()