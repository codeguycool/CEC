# -*- coding: utf-8 -*-

# std
from unittest import TestCase

# 3rd
import mock

# project
from MyScrapy.parsers.atmovies import AtmoviesParser


class TestAtmoviesParser(TestCase):
    def test_get_pageid(self):
        mock_init = mock.Mock(return_value=None)
        AtmoviesParser.__init__ = mock_init
        parser = AtmoviesParser('atmovies', 'http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        pageid = parser.get_pageid('http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        self.assertEqual(pageid, 'fbhk64076934')

    def test_get_title(self):
        mock_init = mock.Mock(return_value=None)
        AtmoviesParser.__init__ = mock_init
        parser = AtmoviesParser('atmovies', 'http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        title = parser.get_title(u'/film/openbox_rating.cfm?filmid=fbhk64076934&filmtitle=特工爺爺')
        self.assertEqual(title, u'特工爺爺')

    def test_get_tokens(self):
        mock_init = mock.Mock(return_value=None)
        AtmoviesParser.__init__ = mock_init
        parser = AtmoviesParser('atmovies', 'http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        tokens = parser.get_tokens(u'片長：106分 上映日期：2016/02/09 廳數 (79) 台北票房：13,472萬')
        self.assertEqual(tokens, {u"片長": u"106分", u"上映日期": "2016/02/09", u"台北票房": u"13,472萬"})

    def test_get_runtimes(self):
        mock_init = mock.Mock(return_value=None)
        AtmoviesParser.__init__ = mock_init
        parser = AtmoviesParser('atmovies', 'http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        runtimes = parser.get_runtimes(u'片長：106分 上映日期：2016/02/09 廳數 (79) 台北票房：13,472萬')
        self.assertEqual(runtimes, '106')

    def test_get_releaseDate(self):
        mock_init = mock.Mock(return_value=None)
        AtmoviesParser.__init__ = mock_init
        parser = AtmoviesParser('atmovies', 'http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        release_dt = parser.get_releaseDate(u'片長：106分 上映日期：2016/02/09 廳數 (79) 台北票房：13,472萬')
        self.assertEqual(release_dt, {'Default': '2016/02/09', 'TW': '2016/02/09'})

    def test_get_releaseDate_with_None(self):
        mock_init = mock.Mock(return_value=None)
        AtmoviesParser.__init__ = mock_init
        parser = AtmoviesParser('atmovies', 'http://ww2.atmovies.com.tw/film/film.cfm?filmid=fbhk64076934')
        release_dt = parser.get_releaseDate(u'片長：106分 廳數 (79) 台北票房：13,472萬')
        self.assertEqual(release_dt, {})

