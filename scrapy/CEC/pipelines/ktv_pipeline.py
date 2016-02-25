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


class KtvPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, dbname='sdb', user="postgres")
        self.cursor = self.conn.cursor()
        self.del_ktv_hot()

    def del_ktv_hot(self):
        try:
            self.cursor.execute("truncate table song_hot")
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()
        except:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()

    def insert_ktv_hot(self, item):
        try:
            # self.cursor.execute("""insert into song_hot
            # select id from songs where title ilike %s and artist ilike %s and lang = %s """,
            #                     ('%'+item['title']+'%', '%'+item['artist']+'%', item['lang']))
            self.cursor.execute("""
            insert into temp(lang, artist, title) values( %(lang)s, %(artist)s, %(title)s)
            """, item)
        except psycopg2.Error:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()
        except:
            scrapy.log.logger.error(traceback.format_exc())
            self.conn.rollback()

    def process_item(self, item, spider):
        self.insert_ktv_hot(item)
        self.conn.commit()
        return item
