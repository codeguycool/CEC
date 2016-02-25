# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# std lib
import datetime
import traceback

# 3rd lib
import psycopg2
import scrapy.log

# proj lib
from CEC.settings import DB_HOST, DB_MDB_NAME


class ContentPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, dbname=DB_MDB_NAME, user="postgres")
        self.cursor = self.conn.cursor()

    def get_md5sum(self, item):
        try:
            self.cursor.execute('Select md5sum From movie_content Where id = %(id)s', item)
            result = self.cursor.fetchone()
            return None if result is None else result[0]
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())

    def insert_content(self, item):
        try:
            self.cursor.execute("""Insert into movie_content(id, source, title, akas, year, imdbid, info_url, content_url, udate, md5sum)
            Values(%(id)s, %(source)s, %(title)s, %(akas)s, %(year)s, %(imdbid)s, %(info_url)s, %(content_url)s,
            %(udate)s, %(md5sum)s)""", item)
            self.conn.commit()
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()


    def update_content(self, item):
        try:
            self.cursor.execute("""Update movie_content set title=%(title)s, akas=%(akas)s, year=%(year)s,
            info_url=%(info_url)s, content_url=%(content_url)s, udate=%(udate)s, md5sum=%(md5sum)s where id=%(id)s""", item)
            self.conn.commit()
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()

    def process_item(self, item, spider):
        md5sum = self.get_md5sum(item)
        item['udate'] = datetime.datetime.utcnow()
        if md5sum is None:
            self.insert_content(item)
        elif md5sum != item['md5sum']:
            self.update_content(item)
        return item
