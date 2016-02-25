# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# std lib
import datetime
import hashlib
import json
import traceback

# 3rd lib
import dateutil.parser
import psycopg2
import scrapy.log

# proj lib
from CEC.settings import DB_HOST, DB_MDB_NAME


class MoviesPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, dbname=DB_MDB_NAME, user="postgres")
        self.cursor = self.conn.cursor()

    def get_md5sum(self, item):
        try:
            self.cursor.execute('Select md5sum From movies Where id = %(id)s', item)
            result = self.cursor.fetchone()
            return None if result is None else result[0]
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())

    def get_keywords(self, item):
        """ 根據spec，將title, akas, genres, directors, stars, year, countries, description 組成一段keyword

        :param item:
        :return:
        """
        keywords = set()
        keywords.add(item['title'])
        for aka in item['akas']:
            keywords.add(aka)
        for genre in item['genres']:
            keywords.add(genre)
        for director in item['directors']:
            keywords.add(director)
        for star in item['stars']:
            keywords.add(star)
        if item['year'] is not None:
            keywords.add(item['year'])
        for country in item['countries']:
            keywords.add(country)
        if item['description'] is not None:
            keywords.add(item['description'])
        keywords = filter(None, keywords)
        return keywords

    def insert_item(self, item):
        try:
            self.cursor.execute("""
            Insert into movies(id, source, title, akas, kind, genres, runtimes, rating,
            posterurl, directors, writers, stars, year, releaseDate, countries,
            languages, description, imdbid, url, md5sum, udate)
            Values(%(id)s, %(source)s,  %(title)s, %(akas)s, %(kind)s, %(genres)s, %(runtimes)s, %(rating)s,
            %(posterurl)s, %(directors)s, %(writers)s, %(stars)s, %(year)s, %(releaseDate)s, %(countries)s,
            %(languages)s, %(description)s, %(imdbid)s, %(url)s, %(md5sum)s, %(udate)s)
            """, item)

            # insert into moviekeyword
            self.cursor.execute("""
            Insert Into movie_keyword(id, kind, keywords, imdbid, source) Values(%s, %s, %s, %s, %s)
            """, (item['id'], item['kind'], ' '.join(self.get_keywords(item)), item['imdbid'], item['source']))

            self.conn.commit()
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()

    def update_item(self, item):
        try:
            self.cursor.execute("""
            Update movies set source=%(source)s, title=%(title)s, akas=%(akas)s, kind=%(kind)s, genres=%(genres)s,
            runtimes=%(runtimes)s, rating=%(rating)s, posterurl=%(posterurl)s, directors=%(directors)s,
            writers=%(writers)s, stars=%(stars)s, year=%(year)s, releaseDate=%(releaseDate)s, countries=%(countries)s,
            languages=%(languages)s, description=%(description)s, imdbid=%(imdbid)s, url=%(url)s, udate=%(udate)s,
            md5sum=%(md5sum)s
            where id=%(id)s""", item)

            # insert into moviekeyword
            self.cursor.execute('delete from movie_keyword where id=%s', (item['id'],))
            self.cursor.execute("""
            Insert Into movie_keyword(id, kind, keywords, imdbid, source) Values(%s, %s, %s, %s, %s)
            """, (item['id'], item['kind'], ' '.join(self.get_keywords(item)), item['imdbid'], item['source']))

            self.conn.commit()
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()

    def process_item(self, item, spider):

        item['md5sum'] = hashlib.md5(json.dumps(item.__dict__, sort_keys=True)).hexdigest()
        # utc time
        item['udate'] = datetime.datetime.utcnow()
        # change datetime format
        for k, v in item['releaseDate'].iteritems():
            try:
                item['releaseDate'][k] = str(dateutil.parser.parse(v))
            except:
                item['releaseDate'][k] = v
        item['releaseDate'] = json.dumps(item['releaseDate'], ensure_ascii=False)

        md5sum = self.get_md5sum(item)
        if md5sum is None:
            self.insert_item(item)
        elif md5sum != item['md5sum']:
            self.update_item(item)
        return item
