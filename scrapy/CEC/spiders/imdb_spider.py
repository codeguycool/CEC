# -*- coding: utf-8 -*-

# std
import os
import re
import sys

# 3rd
import imdb
import psycopg2
import scrapy

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj
import CEC.settings
import CEC.items.movies_item


class IMDBSpider(scrapy.Spider):
    name = 'IMDB'
    allowed_domains = ['imdb.com']
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.movies_pipeline.MoviesPipeline': 300}
    }

    def __init__(self, *args, **kwargs):
        super(IMDBSpider, self).__init__(*args, **kwargs)
        self.ia = imdb.IMDb(accessSystem='sql', uri='postgres://postgres@localhost/IMDB')

    def _getMovie(self, since):
        # get movies if imdb_id is null
        conn = psycopg2.connect(database='IMDB', user='postgres')
        cursor = conn.cursor()
        cursor.execute("""
        select id from title where id not in (select movie_id from movie_info where info_type_id = 3 and info = 'Short')
        and kind_id = 1 and imdb_id is not null order by id limit 1000 OFFSET %d
        """ % (since,))
        return cursor.fetchall()

    def _updateMovie(self, movieid):
        # update imdbid = 0 if can't find imdbid
        conn = psycopg2.connect(database='IMDB', user='postgres')
        cursor = conn.cursor()
        cursor.execute("update title set imdb_id=0 where id=%s", (movieid,))
        conn.commit()

    def _isShortGenre(self, movie):
        if 'genres' in movie.data:
            for genre in movie.data['genres']:
                if genre == 'Short':
                    return True
        return False

    def start_requests(self):
        since = 0
        while True:
            movies = self._getMovie(since)
            if movies:
                for movieid in movies:
                    try:
                        movie = self.ia.get_movie(movieid[0])
                        if self._isShortGenre(movie):
                            self._updateMovie(movieid[0])
                            continue

                        imdbid = self.ia.get_imdbID(movie)
                        if imdbid is not None:
                            imdbid = 'tt%s' % imdbid
                            yield scrapy.Request('http://www.imdb.com/title/%s/' % imdbid, meta={'movieid': movieid[0], 'imdbid': imdbid})
                        else:
                            self._updateMovie(movieid[0])
                    except:
                        pass
                since += 1000
            else:
                break

    def _getRuntime(self, runtime):
        result = re.search(':*(\d+)(?:::)*', runtime)
        if result:
            return int(result.groups()[0])

    def _getReleaseDt(self, releaseDt):
        result = re.search('(\w*):([^:]*)(?:::)*(.*)', releaseDt)
        if result:
            groups = result.groups()
            country = groups[0]
            dt = groups[1]
            memo = groups[2]
            return {'Default': dt, '%s%s' % (country, memo): dt}

    def parse(self, response):
        movieid = response.meta['movieid']
        imdbid = response.meta['imdbid']
        movie = self.ia.get_movie(movieid)
        item = CEC.items.movies_item.MoviesItem()
        item['id'] = 'im_%s' % imdbid
        item['source'] = 'imdb'
        item['title'] = movie.data['title']
        item['imdbid'] = imdbid

        if 'akas' in movie.data:
            item['akas'] = movie.data['akas']
        else:
            item['akas'] = []

        if 'kind' in movie.data:
            item['kind'] = movie.data['kind']
        else:
            item['kind'] = None

        if 'genres' in movie.data:
            item['genres'] = movie.data['genres']
        else:
            item['genres'] = []

        if 'runtimes' in movie.data:
            # fixme: if want to get all runtimes
            item['runtimes'] = self._getRuntime(movie.data['runtimes'][0])
        else:
            item['runtimes'] = None

        if 'release dates' in movie.data:
            item['releaseDate'] = self._getReleaseDt(movie.data['release dates'][0])
        else:
            item['releaseDate'] = {}

        if 'rating' in movie.data:
            item['rating'] = movie.data['rating']
        else:
            item['rating'] = None

        if 'director' in movie.data:
            item['directors'] = [p.data['name'] for p in movie.data['director']]
        else:
            item['directors'] = []

        if 'writer' in movie.data:
            item['writers'] = [p.data['name'] for p in movie.data['writer']]
        else:
            item['writers'] = []

        if 'cast' in movie.data:
            item['stars'] = [p.data['name'] for p in movie.data['cast']]
        else:
            item['stars'] = []

        if 'year' in movie.data:
            item['year'] = movie.data['year']
        else:
            item['year'] = None

        if 'countries' in movie.data:
            item['countries'] = movie.data['countries']
        else:
            item['countries'] = []

        if 'languages' in movie.data:
            item['languages'] = movie.data['languages']
        else:
            item['languages'] = []

        if 'plot' in movie.data:
            item['description'] = movie.data['plot'][0]
        else:
            item['description'] = None

        item['url'] = response.url

        try:
            item['posterurl'] = response.xpath("//td[@id='img_primary']/div[@class='image']/a/img/@src")[0].extract().strip()
        except IndexError:
            item['posterurl'] = None

        yield item


if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(IMDBSpider)
    process.start()