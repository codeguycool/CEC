# -*- coding: utf-8 -*-

# 3rd lib
import scrapy


class MoviesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    source = scrapy.Field()
    title = scrapy.Field(default=None)
    subtitle = scrapy.Field(default=None)
    # 別名
    akas = scrapy.Field(default=[])
    # 種類(movie, tv...)
    kind = scrapy.Field(default=None)
    # 類型(action...)
    genres = scrapy.Field(default=[])
    # 片長
    runtimes = scrapy.Field(default=None)
    # 評分
    rating = scrapy.Field(default=None)
    rated = scrapy.Field()
    posterurl = scrapy.Field(default=None)
    directors = scrapy.Field(default=[])
    writers = scrapy.Field(default=[])
    stars = scrapy.Field(default=[])
    year = scrapy.Field(default=None)
    releaseDate = scrapy.Field(default={})
    countries = scrapy.Field(default=[])
    languages = scrapy.Field(default=[])
    description = scrapy.Field(default=None)
    imdbid = scrapy.Field(default=None)
    url = scrapy.Field()
    md5sum = scrapy.Field()
    udate = scrapy.Field()

default_item = MoviesItem()
default_item['title'] = None
default_item['subtitle'] = None
default_item['akas'] = []
default_item['genres'] = []
default_item['kind'] = None
default_item['runtimes'] = None
default_item['rating'] = None
default_item['posterurl'] = None
default_item['directors'] = []
default_item['writers'] = []
default_item['stars'] = []
default_item['year'] = None
default_item['releaseDate'] = {}
default_item['countries'] = []
default_item['languages'] = []
default_item['description'] = None
default_item['imdbid'] = None
default_item['md5sum'] = None
default_item['udate'] = None