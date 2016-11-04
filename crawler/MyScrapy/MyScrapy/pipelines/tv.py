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
            update drama set source=%(source)s, title=%(title)s, akas=%(akas)s, kind=%(kind)s, genres=%(genres)s,
            posterurl=%(posterurl)s, stars=%(stars)s, year=%(year)s, region=%(region)s, description=%(description)s,
            url=%(url)s, play_urls=%(play_urls)s, update_eps=%(update_eps)s, total_eps=%(total_eps)s,
            completed=%(completed)s, dbid=%(dbid)s, rdate=%(rdate)s, udate=%(udate)s, md5sum=%(md5sum)s
            where id=%(id)s and md5sum != %(md5sum)s
            returning %(id)s as id
        )
        Insert into drama(id, source, title, akas, kind, genres, posterurl, stars, year,
        region, description, url, play_urls, update_eps, total_eps, completed, dbid,
        rdate, udate, md5sum)
        Select %(id)s, %(source)s,  %(title)s, %(akas)s, %(kind)s, %(genres)s, %(posterurl)s, %(stars)s, %(year)s,
        %(region)s, %(description)s, %(url)s, %(play_urls)s, %(update_eps)s, %(total_eps)s, %(completed)s, %(dbid)s,
        %(rdate)s, %(udate)s, %(md5sum)s
        where not exists (
            select md5sum from drama where id = %(id)s
        )
        """, item)

        conn.commit()
    except Exception:
        conn.rollback()
        raise


def cleandb():
    conn = psycopg2.connect(host=LMDB_DB_HOST, dbname=LMDB_DB_NAME, user=LMDB_DB_ACCOUNT)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        delete from drama where source = 'douban' and dbid is null;
        delete from drama where source = 'imdb' and dbid is null;
        """)

        conn.commit()
    except Exception:
        conn.rollback()
        raise


class TvPipeline(object):

    def process_item(self, item, spider):
        try:
            save2db(item)
        except Exception:
            logging.error(traceback.format_exc() + '\r\n' + str(item))
        return item

    def close_spider(self, spider):
        try:
            cleandb()
        except Exception:
            logging.error(traceback.format_exc())
