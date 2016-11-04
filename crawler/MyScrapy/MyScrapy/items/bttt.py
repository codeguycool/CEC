# -*- coding: utf-8 -*-

# 3rd
import scrapy


class BtTTItem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    akas = scrapy.Field()
    imdbid = scrapy.Field()
    info_url = scrapy.Field()
    content_urls = scrapy.Field()
    rdate = scrapy.Field()
    udate = scrapy.Field()
    md5sum = scrapy.Field()
