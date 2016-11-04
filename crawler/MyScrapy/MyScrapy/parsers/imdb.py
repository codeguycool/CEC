# -*- coding: utf-8 -*-

# std
import re

# project
from MyCrontab.updateimdb.imdbpy import IMDbPy
from MyScrapy.items.tv import TvItem
from MyScrapy.items.movie import MovieItem


class ImdbMovieParser(object):

    def __init__(self, url):
        self.url = url
        self.imdbid = self.get_imdbid()
        self.item = MovieItem()

    def parse(self):
        imdbpy = IMDbPy()
        movie = imdbpy.get_movie(self.imdbid)
        self.item = movie

    def get_imdbid(self):
        result = re.findall('www.imdb.com/title/(tt\d{7})/', self.url)
        if result:
            return result[0]


class ImdbTvParser(object):

    def __init__(self, imdbid, kind):
        imdbpy = IMDbPy()
        movie = imdbpy.get_movie(imdbid)
        item = TvItem()
        item['source'] = 'imdb'
        item['id'] = 'im_' + movie['imdbid']
        item['kind'] = kind
        item['title'] = movie['title']
        item['akas'] = movie['akas']
        item['stars'] = movie['stars']
        item['posterurl'] = movie['posterurl']
        item['year'] = movie['year']
        item['genres'] = movie['genres']
        item['region'] = movie['countries'][0] if len(movie['countries']) else None
        item['description'] = movie['description']
        item['url'] = movie['url']
        self.item = item
