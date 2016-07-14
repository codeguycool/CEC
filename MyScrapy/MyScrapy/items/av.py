# -*- coding: utf-8 -*-

# 3rd
import scrapy


class AvItem(scrapy.Item):
    id = scrapy.Field()
    code = scrapy.Field()  # 番號
    title = scrapy.Field()
    posterurl = scrapy.Field()
    duration = scrapy.Field()
    performer = scrapy.Field()  # 出演者
    category = scrapy.Field()
    rating = scrapy.Field()
    maker = scrapy.Field()  # 廠商
    series = scrapy.Field()  # 系列
    date = scrapy.Field()  # 商品発売日
    date2 = scrapy.Field()  # 配信開始日
    description = scrapy.Field()
    samples = scrapy.Field()  # 截圖
    url = scrapy.Field()
    md5sum = scrapy.Field()
    udate = scrapy.Field()

    def get_keywords(self):
        """

        :return:
        """
        keywords = set()
        keywords.add(self['id'])
        keywords.add(self['title'])
        if self['code'] is not None:
            keywords.add(self['code'])
        if self['maker'] is not None:
            keywords.add(self['maker'])
        if self['series'] is not None:
            keywords.add(self['series'])
        for c in self['category']:
            keywords.add(c)
        for p in self['performer']:
            keywords.add(p)
        keywords = filter(None, keywords)
        return keywords
