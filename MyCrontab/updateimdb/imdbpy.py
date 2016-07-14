# -*- coding: utf-8 -*-

# std
import json
import re
import time

# 3rd
import imdb
import requests

# project
from lib.log import logger
from lib.utils import get_useragent
from MyScrapy.items.movie import MovieItem
from MyScrapy.pipelines.movie import save2db as pipe2db


class IMDbPy(object):

    def __init__(self, uri=None, tmdbapikey=None):
        self.uri = uri

        if self.uri:
            from settings import API_KEY_TMDB
            self.tmdbapikey = tmdbapikey if tmdbapikey is not None else API_KEY_TMDB
            self.imdb_access = imdb.IMDb(accessSystem='sql', uri=uri)
        else:
            self.imdb_access = imdb.IMDb()

    def get_movie(self, imdbid, movieid=None):
        """

        :param imdbid: tt0111161
        :param movieid:
        :return:
        """

        if imdbid is None:
            raise Exception('imdbid is None')

        if self.uri:
            if movieid is None:
                raise Exception('movieid is None')

            imdbpymovie = self.imdb_access.get_movie(movieid)
            return SQLMovie(imdbpymovie=imdbpymovie, imdbid=imdbid, tmdbapikey=self.tmdbapikey)
        else:
            imdbid_for_imdbpy = int(imdbid[2:])
            self.imdb_access.urlOpener.set_header('User-Agent', get_useragent())
            imdbpymovie = self.imdb_access.get_movie(imdbid_for_imdbpy)
            # fixme: imdb block imdbpy
            if 'title' in imdbpymovie.data and imdbpymovie.data['title'] == 'How Did You Get Here?':
                raise Exception("imdb block imdbpy")
            if imdbpymovie.data == {}:
                raise Exception("can't find movie")
            return HttpMovie(imdbpymovie=imdbpymovie, imdbid=imdbid)

    def get_imdbid(self, movieid):
        """ 取imdbid

        :param movieid:
        :return:
        """
        if self.uri:
            return self.imdb_access.get_imdbMovieID(movieid)
        else:
            return movieid

    def is_network_ok(self):
        """ 檢查imdb網路是否正常

        利用'tt0111161'去檢查能否正常取回資訊

        :return:
        """
        try:
            imdb_top_1 = 'tt0111161'
            self.get_movie(imdb_top_1)
            return True
        except Exception:
            return False


class BaseMovie(MovieItem):

    def __init__(self, imdbpymovie, imdbid):

        super(BaseMovie, self).__init__()

        if 'akas' in imdbpymovie.data:
            self['akas'] = [BaseMovie.get_akas(akas) for akas in imdbpymovie.data['akas']]
        else:
            self['akas'] = []

        # fixme: 如果 imdbpymovie 不止是 movie 的話

        # 將所有分類的 movie 都轉成 movie， video movie => movie
        self['kind'] = 'movie'

        if 'genres' in imdbpymovie.data:
            self['genres'] = imdbpymovie.data['genres']
        else:
            self['genres'] = []

        if 'runtimes' in imdbpymovie.data:
            # fixme: 如果需要全部的 runtime 資訊
            self['runtimes'] = BaseMovie.get_runtime(imdbpymovie.data['runtimes'][0])
        else:
            self['runtimes'] = None

        if 'release dates' in imdbpymovie.data:
            # fixme: 如果需要全部的 release dates 資訊
            self['releaseDate'] = BaseMovie.get_releasedate(imdbpymovie.data['release dates'][0])
        else:
            self['releaseDate'] = {}

        if 'rating' in imdbpymovie.data:
            self['rating'] = imdbpymovie.data['rating']
        else:
            self['rating'] = None

        if 'director' in imdbpymovie.data:
            self['directors'] = [p.data['name'] for p in imdbpymovie.data['director']]
        else:
            self['directors'] = []

        if 'writer' in imdbpymovie.data:
            self['writers'] = [p.data['name'] for p in imdbpymovie.data['writer']]
        else:
            self['writers'] = []

        if 'cast' in imdbpymovie.data:
            self['stars'] = [p.data['name'] for p in imdbpymovie.data['cast']]
        else:
            self['stars'] = []

        if 'year' in imdbpymovie.data:
            self['year'] = str(imdbpymovie.data['year'])
        else:
            self['year'] = None

        if 'countries' in imdbpymovie.data:
            self['countries'] = imdbpymovie.data['countries']
        else:
            self['countries'] = []

        if 'languages' in imdbpymovie.data:
            self['languages'] = [BaseMovie.get_lang(languages) for languages in imdbpymovie.data['languages']]
        else:
            self['languages'] = []

        if 'plot' in imdbpymovie.data:
            self['description'] = imdbpymovie.data['plot'][0]
        else:
            self['description'] = None

        self['source'] = 'imdb'
        self['id'] = 'im_' + imdbid
        self['imdbid'] = imdbid
        self['title'] = imdbpymovie.data['title']
        self['url'] = 'http://www.imdb.com/title/%s/' % imdbid
        self['posterurl'] = self.get_posterurl(imdbpymovie=imdbpymovie)
        self['thumbnailurl'] = self.get_thumbnailurl(imdbpymovie=imdbpymovie)

        if 'season' in imdbpymovie.data:
            self['title'] = '%s (season %d)' % (
                imdbpymovie.data['episode of'].data['title'], imdbpymovie.data['season']
            )

    def save2db(self, host, dbname):
        """ 儲存到db

        :param host:
        :param dbname:
        :return:
        """
        pipe2db(self, host, dbname)

    @classmethod
    def get_akas(cls, akas):
        """ Baby (1973)::(Italy)

        :param akas:
        :return:
        """
        result = re.search('(.*)(?:::).*', akas)
        if result:
            return result.groups()[0]
        else:
            return akas

    @classmethod
    def get_runtime(cls, runtime):
        """ 處理imdb的runtime

        :param runtime:
        :return:
        """
        result = re.search(':*(\d+)(?:::)*', runtime)
        if result:
            return int(result.groups()[0])

    @classmethod
    def get_releasedate(cls, releasedate):
        """ 處理imdb的release date

        :param releasedate:
        :return:
        """
        result = re.search('(\w*):([^:]*)(?:::)*(.*)', releasedate)
        if result:
            groups = result.groups()
            country = groups[0]
            dt = groups[1]
            memo = groups[2]
            return {'Default': dt, '%s%s' % (country, memo): dt}

    @classmethod
    def get_lang(cls, lang):
        """ English::(intertitles)}

        :param lang:
        :return:
        """
        result = re.search('(.*)(?:::).*', lang)
        if result:
            return result.groups()[0]
        else:
            return lang

    def get_thumbnailurl(self, imdbpymovie):
        raise NotImplementedError

    def get_posterurl(self, imdbpymovie):
        raise NotImplementedError


class HttpMovie(BaseMovie):

    def __init__(self, imdbpymovie, imdbid):
        super(HttpMovie, self).__init__(imdbpymovie, imdbid)

    @classmethod
    def get_posterurl_by_width(cls, imdbpymovie, width):
        if 'cover url' in imdbpymovie.data:
            posterurl = imdbpymovie.data['cover url']
            index = posterurl.find('._V1')
            return '%s.UX%d.jpg' % (imdbpymovie.data['cover url'][:index] if index > 0 else imdbpymovie.data['cover url'], width)
        else:
            return None

    def get_thumbnailurl(self, imdbpymovie):
        """ 取得海報小圖

        :param imdbpymovie:
        :return:
        """
        return HttpMovie.get_posterurl_by_width(imdbpymovie, 300)

    def get_posterurl(self, imdbpymovie):
        """ 取得海報大圖

        :param imdbpymovie:
        :return:
        """
        return HttpMovie.get_posterurl_by_width(imdbpymovie, 600)


class SQLMovie(BaseMovie):

    def __init__(self, imdbpymovie, imdbid, tmdbapikey):
        self._imdbid = imdbid
        self._tmdbapikey = tmdbapikey
        self._tmdbresult = None
        super(SQLMovie, self).__init__(imdbpymovie, imdbid)

    def get_posterurl_by_width(self, imdbpymovie, width):
        if self._tmdbresult is None:
            # fixme: 如果要全部都跑的話，記得修改條件
            # 符合2個條件就執行
            matchcount = 0
            matchcount = matchcount + 1 if self['directors'] != [] else matchcount
            matchcount = matchcount + 1 if self['stars'] != [] else matchcount
            matchcount = matchcount + 1 if self['stars'] != [] else matchcount
            if matchcount > 1:
                url = 'http://api.themoviedb.org/3/find/%s?external_source=imdb_id&api_key=%s' % (self._imdbid, self._tmdbapikey)
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    self._tmdbresult = json.loads(response.text)
                else:
                    time.sleep(5)
                    logger.warning('url: %s, status: %d' % (url, response.status_code))

        if self._tmdbresult is not None:
            if len(self._tmdbresult['movie_results']) == 1 and self._tmdbresult['movie_results'][0]['poster_path']:
                return 'http://image.tmdb.org/t/p/w%d%s' % (width, self._tmdbresult['movie_results'][0]['poster_path'])

    def get_thumbnailurl(self, imdbpymovie):
        """ 取得海報小圖

        :param imdbpymovie:
        :return:
        """
        return self.get_posterurl_by_width(imdbpymovie, 300)

    def get_posterurl(self, imdbpymovie):
        """ 取得海報小圖

        :param imdbpymovie:
        :return:
        """
        return self.get_posterurl_by_width(imdbpymovie, 600)
