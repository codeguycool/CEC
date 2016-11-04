# -*- coding: utf-8 -*-

# std
import datetime
import hashlib
import json

# 3rd
import scrapy


class TvItem(scrapy.Item):
    source = scrapy.Field()
    id = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    akas = scrapy.Field()
    posterurl = scrapy.Field()
    stars = scrapy.Field()
    genres = scrapy.Field()
    kind = scrapy.Field()
    region = scrapy.Field()
    year = scrapy.Field()
    description = scrapy.Field()
    update_eps = scrapy.Field()  # 更新集數
    total_eps = scrapy.Field()  # 全部集數
    completed = scrapy.Field()  # 是否完結
    rdate = scrapy.Field()  # tv 更新日期
    udate = scrapy.Field()  # db 更新日期
    url = scrapy.Field()
    play_urls = scrapy.Field()  # 播放來源
    imdbid = scrapy.Field()  # imdbid
    dbid = scrapy.Field()  # 豆瓣ID
    md5sum = scrapy.Field()

    def pre_process(self):
        # 去除空白
        for key in self.keys():
            if isinstance(self[key], list):
                self[key] = [value.strip() for value in self[key] if isinstance(value, basestring)]
                self[key] = filter(None, self[key])
            elif isinstance(self[key], basestring):
                self[key] = self[key].strip()

        # md5sum, 必須在udate前做計算
        self['md5sum'] = hashlib.md5(json.dumps(self._values, sort_keys=True)).hexdigest()

        # utc time
        self['udate'] = datetime.datetime.utcnow()

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

    def copy_from(self, source):
        """ 將資訊從source中取得並更新自己

        :param source:
        :return:
        """
        if source is not None:
            self['rdate'] = source['rdate']
            self['completed'] = source['completed']
            self['update_eps'] = source['update_eps']
            self['total_eps'] = source['total_eps']
            self['play_urls'] = source['play_urls']
            self['dbid'] = source['dbid']
