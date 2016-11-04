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


class MovieContentPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=LMDB_DB_HOST, dbname=LMDB_DB_NAME, user=LMDB_DB_ACCOUNT)
        self.cursor = self.conn.cursor()

    def save_item(self, item):
        try:
            self.cursor.execute("""
            with upsert as (
                update movie_content set title=%(title)s, akas=%(akas)s, year=%(year)s, info_url=%(info_url)s,
                content_url=%(content_url)s, udate=%(udate)s, md5sum=%(md5sum)s
                where id=%(id)s and md5sum != %(md5sum)s
                returning %(id)s as id
            )
            Insert into movie_content(id, source, title, akas, year, imdbid, info_url, content_url, udate, md5sum)
            select %(id)s, %(source)s, %(title)s, %(akas)s, %(year)s, %(imdbid)s, %(info_url)s, %(content_url)s,
            %(udate)s, %(md5sum)s
            where not exists (
                select id from movie_content where id = %(id)s
            )
            """, item)
            self.conn.commit()
        except Exception:
            logging.error(traceback.format_exc() + '\r\n' + str(item))
            self.conn.rollback()

    def process_item(self, item, spider):
        self.save_item(item)
        return item
