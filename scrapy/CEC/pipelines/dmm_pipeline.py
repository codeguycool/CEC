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
import psycopg2
import scrapy.log

# proj lib
from CEC.settings import DB_HOST, DB_ADB_NAME


class DmmDbPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, dbname=DB_ADB_NAME, user="postgres")
        self.cursor = self.conn.cursor()

    def get_md5sum(self, item):
        try:
            self.cursor.execute('Select md5sum From video where id = %(id)s', item)
            result = self.cursor.fetchone()
            return None if result is None else result[0]
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())

    def get_keywords(self, item):
        """

        :param item:
        :return:
        """
        keywords = set()
        keywords.add(item['id'])
        keywords.add(item['title'])
        if item['performer'] is not None:
            keywords.add(item['performer'])
        if item['maker'] is not None:
            keywords.add(item['maker'])
        if item['series'] is not None:
            keywords.add(item['series'])
        for c in item['category']:
            keywords.add(c)
        keywords = filter(None, keywords)
        return keywords

    def insert_item(self, item):
        try:
            self.cursor.execute("""
            insert into video(id, title, posterurl, duration, performer, category, rating, maker,
            series, date, description, samples, url, md5sum, udate)
            values(%(id)s, %(title)s, %(posterurl)s, %(duration)s, %(performer)s, %(category)s, %(rating)s, %(maker)s,
            %(series)s, %(date)s, %(description)s, %(samples)s, %(url)s, %(md5sum)s, %(udate)s)
            """, item)

            self.cursor.execute("""
            insert into video_keyword(id, keywords) values(%s, %s)
            """, (item['id'], ' '.join(self.get_keywords(item))))

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
            Update video set title=%(title)s, posterurl=%(posterurl)s, duration=%(duration)s, performer=%(performer)s,
            category=%(category)s, rating=%(rating)s, maker=%(maker)s, series=%(series)s, date=%(date)s,
            description=%(description)s, samples=%(samples), url=%(url)s, md5sum=%(md5sum)s, udate=%(udate)s
            where id=%(id)s""", item)

            self.cursor.execute("""
            Update video_keyword set keywords=%s where id=%s
            """, (' '.join(self.get_keywords(item)), item['id']))

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

        md5sum = self.get_md5sum(item)
        if md5sum is None:
            self.insert_item(item)
        elif md5sum != item['md5sum']:
            self.update_item(item)
        return item
