# -*- coding: utf-8 -*-

# std
import datetime
import hashlib
import json

# 3rd
import dateutil.parser
import scrapy


class MovieItem(scrapy.Item):
    id = scrapy.Field()
    source = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    akas = scrapy.Field()  # 別名
    kind = scrapy.Field()  # 種類(movie, tv...), 目前只剩movie有用
    genres = scrapy.Field()  # 類型(action...)
    runtimes = scrapy.Field()  # 片長
    rating = scrapy.Field()  # 評分
    rated = scrapy.Field()  # 分級 (disable)
    posterurl = scrapy.Field()
    thumbnailurl = scrapy.Field()
    directors = scrapy.Field()
    writers = scrapy.Field()
    stars = scrapy.Field()
    year = scrapy.Field()
    releaseDate = scrapy.Field()
    countries = scrapy.Field()
    languages = scrapy.Field()
    description = scrapy.Field()
    imdbid = scrapy.Field()
    url = scrapy.Field()
    md5sum = scrapy.Field()
    udate = scrapy.Field()

    def __init__(self):
        scrapy.Item.__init__(self)
        self['title'] = None
        self['subtitle'] = None
        self['akas'] = []
        self['genres'] = []
        self['kind'] = None
        self['runtimes'] = None
        self['rating'] = None
        self['posterurl'] = None
        self['thumbnailurl'] = None
        self['directors'] = []
        self['writers'] = []
        self['stars'] = []
        self['year'] = None
        self['releaseDate'] = {}
        self['countries'] = []
        self['languages'] = []
        self['description'] = None
        self['imdbid'] = None
        self['md5sum'] = None
        self['udate'] = None

    def pre_process(self):

        # 去除空白
        for key in self.keys():
            if isinstance(self[key], list):
                self[key] = [value.strip() for value in self[key] if isinstance(value, basestring)]
                self[key] = filter(None, self[key])
            elif isinstance(self[key], basestring):
                self[key] = self[key].strip()
                self[key] = None if self[key] == '' else self[key]

        # md5sum, 必須在udate前做計算
        self['md5sum'] = hashlib.md5(json.dumps(self._values, sort_keys=True)).hexdigest()

        # utc time
        self['udate'] = datetime.datetime.utcnow()

        # 如果releaseDate為空，且year不為空，將year的值給releaseDate['Default']
        if not self['releaseDate'] and self['year'] is not None:
            self['releaseDate'] = {'Default': self['year']}

        # change datetime format
        for k, v in self['releaseDate'].iteritems():
            try:
                self['releaseDate'][k] = str(dateutil.parser.parse(v))
            except:
                self['releaseDate'][k] = v

        self['releaseDate'] = json.dumps(self['releaseDate'], ensure_ascii=False)

    def get_keywords(self):
        """ 根據spec，將title, akas, genres, directors, stars, year, countries, description 組成一段keyword

        :return:
        """
        keywords = set()
        keywords.add(self['title'])
        for aka in self['akas']:
            keywords.add(aka)
        for genre in self['genres']:
            keywords.add(genre)
        for director in self['directors']:
            keywords.add(director)
        for star in self['stars']:
            keywords.add(star)
        if self['year'] is not None:
            keywords.add(self['year'])
        for country in self['countries']:
            keywords.add(country)
        if self['description'] is not None:
            keywords.add(self['description'])
        keywords = filter(None, keywords)
        return keywords
