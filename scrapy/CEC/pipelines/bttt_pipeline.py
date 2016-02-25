# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# std lib
import json
import traceback

# 3rd lib
import psycopg2
import scrapy.log

# proj lib
from CEC.settings import DB_HOST, DB_MDB_NAME


class BtTTPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, dbname=DB_MDB_NAME, user="postgres")
        self.cursor = self.conn.cursor()

    def is_exist_movies(self, oid):
        try:
            self.cursor.execute('Select id From bttt Where id = %s', (oid,))
            return self.cursor.fetchone() is not None
        except Exception:
            scrapy.log.logger.error(traceback.format_exc())

    def insert_movies(self, item):
        try:
            item['content_urls'] = json.dumps(item['content_urls'], ensure_ascii=False)
            self.cursor.execute("""Insert into bttt(id, title, udate, imdbid, info_url, content_urls)
            Values(%(id)s, %(title)s, %(udate)s, %(imdbid)s, %(info_url)s, %(content_urls)s)""", item)
            self.conn.commit()
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()

    def process_item(self, item, spider):
        if not self.is_exist_movies(item['id']):
            self.insert_movies(item)
        return item
