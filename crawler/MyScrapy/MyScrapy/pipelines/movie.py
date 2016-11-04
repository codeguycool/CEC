# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# std
import logging
import traceback

# 3rd
import psycopg2

# project
from MyScrapy.settings import LMDB_DB_NAME, LMDB_DB_HOST, LMDB_DB_PORT, LMDB_DB_ACCOUNT


def save2db(item, host=LMDB_DB_HOST, dbname=LMDB_DB_NAME, user=LMDB_DB_ACCOUNT):
    item.pre_process()

    conn = psycopg2.connect(host=host, dbname=dbname, user=user)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        with upsert as (
            update movies set source=%(source)s, title=%(title)s, akas=%(akas)s, kind=%(kind)s, genres=%(genres)s,
            runtimes=%(runtimes)s, rating=%(rating)s, posterurl=%(posterurl)s, thumbnailurl=%(thumbnailurl)s,
            directors=%(directors)s, writers=%(writers)s, stars=%(stars)s, year=%(year)s, releaseDate=%(releaseDate)s,
            countries=%(countries)s, languages=%(languages)s, description=%(description)s, imdbid=%(imdbid)s,
            url=%(url)s, udate=%(udate)s, md5sum=%(md5sum)s
            where id=%(id)s and md5sum != %(md5sum)s
            returning %(id)s as id
        )
        Insert into movies(id, source, title, akas, kind, genres, runtimes, rating, posterurl,
        thumbnailurl, directors, writers, stars, year, releaseDate, countries,
        languages, description, imdbid, url, md5sum, udate)
        Select %(id)s, %(source)s,  %(title)s, %(akas)s, %(kind)s, %(genres)s, %(runtimes)s, %(rating)s, %(posterurl)s,
        %(thumbnailurl)s, %(directors)s, %(writers)s, %(stars)s, %(year)s, %(releaseDate)s, %(countries)s,
        %(languages)s, %(description)s, %(imdbid)s, %(url)s, %(md5sum)s, %(udate)s
        where not exists (
            select md5sum from movies where id = %(id)s
        )
        """, item)

        # insert into moviekeyword
        cursor.execute('delete from movie_keyword where id=%s', (item['id'],))
        cursor.execute("""
        Insert Into movie_keyword(id, kind, keywords, imdbid, source) Values(%s, %s, %s, %s, %s)
        """, (item['id'], item['kind'], ' '.join(item.get_keywords()), item['imdbid'], item['source']))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


class MoviePipeline(object):

    def process_item(self, item, spider):
        try:
            save2db(item)
        except Exception:
            logging.error(traceback.format_exc() + '\r\n' + str(item))
        return item
