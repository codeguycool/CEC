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


class BtTTPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=LMDB_DB_HOST, dbname=LMDB_DB_NAME, user=LMDB_DB_ACCOUNT)
        self.cursor = self.conn.cursor()

    def del_existmovie(self, item):
        try:
            self.cursor.execute('Delete from bttt where imdbid = %s and rdate < %s', (item['imdbid'], item['rdate']))
        except Exception:
            raise

    def save_database(self, item):
        try:
            self.cursor.execute("""
            insert into bttt(id, title, imdbid, info_url, content_urls, rdate, udate, md5sum)
            select %(id)s, %(title)s, %(imdbid)s, %(info_url)s, %(content_urls)s, %(rdate)s, %(udate)s, %(md5sum)s
            where not exists (
                select id from bttt where id = %(id)s
            )
            """, item)
            self.conn.commit()
        except psycopg2.Error:
            logging.error(traceback.format_exc() + '\r\n' + str(item))
            self.conn.rollback()

    def process_item(self, item, spider):
        # 同一部電影可能會出現2次，改用imdbid做唯一值
        self.del_existmovie(item)
        self.save_database(item)
        return item
