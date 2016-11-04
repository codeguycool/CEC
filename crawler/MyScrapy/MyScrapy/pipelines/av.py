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
from MyScrapy.settings import LADB_DB_NAME, LADB_DB_HOST, LADB_DB_PORT, LADB_DB_ACCOUNT


class AvPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=LADB_DB_HOST, dbname=LADB_DB_NAME, user=LADB_DB_ACCOUNT)
        self.cursor = self.conn.cursor()

    def save_item(self, item):
        try:
            self.cursor.execute("""
            with upsert as (
                update video set code=%(code)s, title=%(title)s, posterurl=%(posterurl)s, duration=%(duration)s,
                performer=%(performer)s, category=%(category)s, rating=%(rating)s, maker=%(maker)s, series=%(series)s,
                date=%(date)s, date2=%(date2)s, description=%(description)s, samples=%(samples)s, url=%(url)s,
                md5sum=%(md5sum)s, udate=%(udate)s
                where id=%(id)s and md5sum != %(md5sum)s
                returning %(id)s as id
            )
            Insert into video(id, code, title, posterurl, duration, performer, category, rating,
            maker, series, date, date2, description, samples, url, md5sum, udate)
            select %(id)s, %(code)s, %(title)s, %(posterurl)s, %(duration)s, %(performer)s, %(category)s, %(rating)s,
            %(maker)s, %(series)s, %(date)s, %(date2)s, %(description)s, %(samples)s, %(url)s, %(md5sum)s, %(udate)s
            where not exists (
                select id from video where id = %(id)s
            )
            """, item)

            self.cursor.execute('delete from video_keyword where id=%s', (item['id'],))
            self.cursor.execute("""
            insert into video_keyword(id, keywords) values(%s, %s)
            """, (item['id'], ' '.join(item.get_keywords())))

            self.conn.commit()
        except Exception:
            logging.error(traceback.format_exc() + '\r\n' + str(item))
            self.conn.rollback()

    def process_item(self, item, spider):
        self.save_item(item)
        return item
