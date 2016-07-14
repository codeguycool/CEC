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
from MyScrapy.settings import LSDB_DB_NAME, LSDB_DB_HOST, LSDB_DB_PORT, LSDB_DB_ACCOUNT


def cleardb():
    conn = psycopg2.connect(host=LSDB_DB_HOST, dbname=LSDB_DB_NAME, user=LSDB_DB_ACCOUNT)
    try:
        cursor = conn.cursor()
        cursor.execute('truncate table song_list')
        conn.commit()
    except Exception:
        logging.error(traceback.format_exc())
        conn.rollback()


class KtvPipeline(object):

    def __init__(self):
        self.conn = psycopg2.connect(host=LSDB_DB_HOST, dbname=LSDB_DB_NAME, user=LSDB_DB_ACCOUNT)
        self.cursor = self.conn.cursor()

    def insert_item(self, item):
        try:
            # 如果找不到keymd5就新增
            self.cursor.execute("""
            insert into songs(source, title, lang, artist, keywords, keymd5, udate)
            select %(source)s, %(title)s, %(lang)s, %(artist)s, %(keywords)s, %(keymd5)s, %(udate)s
            where not exists (
                select keymd5 from songs where keymd5=%(keymd5)s
            )
            """, item)

            # song_list
            if item.islist():
                self.cursor.execute("""
                insert into song_list(source, type, lang, title, artist, keymd5, rank, udate)
                select %(source)s, %(type)s, %(lang)s, %(title)s, %(artist)s, %(keymd5)s, %(rank)s, %(udate)s
                where not exists (
                    select keymd5 from song_list where source = %(source)s and type = %(type)s and keymd5 = %(keymd5)s
                )
                """, item)

            # song_content
            if item['youtube']:
                # 當 keymd5存在且md5sum不相同時進行更新 or 當找不到keymd5時則進行插入
                self.cursor.execute("""
                with upsert as (
                    update song_content set source=%(source)s, fullname=%(fullname)s, poster_url=%(poster_url)s,
                    uploader=%(uploader)s, upload_date=%(upload_date)s, duration=%(duration)s,
                    description=%(description)s, play_url=%(play_url)s, content=%(content)s, keymd5=%(keymd5)s,
                    md5sum=%(md5sum)s, udate=%(udate)s
                    where source = %(source)s and keymd5 = %(keymd5)s and md5sum != %(md5sum)s
                    returning %(source)s as source, %(keymd5)s as keymd5
                )
                insert into song_content(source, fullname, poster_url, uploader, upload_date, duration,
                description, play_url, content, keymd5, md5sum, udate)
                select %(source)s, %(fullname)s, %(poster_url)s, %(uploader)s, %(upload_date)s, %(duration)s,
                %(description)s, %(play_url)s, %(content)s, %(keymd5)s, %(md5sum)s, %(udate)s
                where not exists(
                    select keymd5 from song_content where source = %(source)s and keymd5 = %(keymd5)s
                )
                """, item['youtube'])
            self.conn.commit()
        except Exception:
            logging.error(traceback.format_exc())
            self.conn.rollback()

    def process_item(self, item, spider):
        self.insert_item(item)
        return item
