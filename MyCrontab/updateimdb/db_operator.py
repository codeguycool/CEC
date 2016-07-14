# -*- coding: utf-8 -*-

# 3rd
import psycopg2


class IMDBOperator(object):
    """ IMDB資料庫的操作元

    """

    def __init__(self, host, db, usrname='postgres'):
        self.HOST = host
        self.DB = db
        self.USERNAME = usrname
        self.LIMIT = 5000
        self.URI = 'postgres://postgres@%s/%s' % (self.HOST, self.DB)

    def get_null_imdbid_movies(self, limit=5000):
        """ 找出IMDBID為空的電影，並且不是短片的類型

        :param limit: 最多取回多少筆資料
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            select id from title where kind_id = 1 and imdb_id is null and id not in (
                select distinct movie_id from movie_info where info_type_id = 3 and info = 'Short'
            )
            limit %s
            """ % limit)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def set_imdbid_as_zero(self, movieid):
        """ 將電影的IMDBID設為0，才不會重複處理

        :param movieid:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        cursor.execute('update title set imdb_id = 0 where id=%s' % movieid)
        conn.commit()

    def remove_duplicate_imdb(self):
        """ 將有重覆IMDBID的處理設為0

        重覆的IMDBID可能造成資料的錯誤，將其設為0; 避免取用

        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        cursor.execute("""
        update title set imdb_id = 0
        where imdb_id in (select imdb_id from title where imdb_id != 0 group by imdb_id
        having count(imdb_id) > 1)
        """)
        conn.commit()

    def get_movies_to_export_lmdb(self, since, limit=5000):
        """ 找出要匯出到LMDB的電影

        :param since:
        :param limit:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            select id, imdb_id from title where kind_id = 1 and imdb_id is not null and imdb_id != 0
            and id not in (
                select distinct movie_id from movie_info where info_type_id = 3 and info = 'Short'
            )
            order by id desc
            limit %s
            offset %s
            """ % (limit, since))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def imdbid2csv(self, csvpath):
        """ 匯出imdbid到csv

        :param csvpath: 要匯出imdb的路徑
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            with open(csvpath, mode='w') as f:
                cursor.copy_expert("""
                copy (
                    select distinct 'tt' || lpad(imdb_id::text, 7, '0') from title
                    where kind_id = 1 and imdb_id is not null and imdb_id != 0
                    and id not in (
                        select distinct movie_id from movie_info where info_type_id = 3 and info = 'Short'
                    )
                ) to stdout
                """, f)
        finally:
            cursor.close()
            conn.close()


class LMDBOperator(object):
    """ LMDB資料庫的操作元

    """

    def __init__(self, host, db, usrname='postgres'):
        self.HOST = host
        self.DB = db
        self.USERNAME = usrname
        self.LIMIT = 5000

    def import_imdbid(self, csvpath):
        """ 匯入imdbid

        :param csvpath:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            with open(csvpath) as f:
                cursor.execute("""
                drop table if exists movie_imdb;
                create table movie_imdb(
                    imdbid char(9),
                    constraint movie_imdb_pk primary key (imdbid)
                );
                """)
                cursor.copy_expert(""" copy movie_imdb from stdin
                """, f)
                conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_movies_for_imdb_reparse(self, limit=5000, since=0):
        """ 找出需要到imdb網站parse的電影的imdbid

        以其他來源(開眼、豆瓣)的imdbid為依據，重新爬imdb網站

        :param limit:
        :param since:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            select distinct imdbid from movies
            where source != 'imdb'
            and imdbid is not null
            order by imdbid desc
            limit %s
            offset %s
            """ % (limit, since))

            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_imdb_miss_movies(self, limit=5000, since=0):
        """ 找出其他來源(開眼、豆瓣)有，IMDB沒有的電影

        :param limit:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            select distinct imdbid from movies
            where source != 'imdb' and imdbid is not null and kind = 'movie'
            and not exists (
            select imdbid from movies m where source = 'imdb' and imdbid = movies.imdbid
            )
            limit %s
            offset %s
            """ % (limit, since))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def clear_imdbid(self, imdbid):
        """ 清除不正確的IMDBID

        :param imdbid:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            cursor.execute('update movies set imdbid=null where imdbid=%s', (imdbid,))
            cursor.execute("""
            with upsert as (
                update movie_err_imdb set count = count+1
                where imdbid=%(imdbid)s
                RETURNING imdbid
            )
            select %(imdbid)s from movie_err_imdb
            where not exists(
                select * from movie_err_imdb where imdbid=%(imdbid)s
            )
            """, {'imdbid': imdbid})
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def is_error_imdbid_movie(self, imdbid):
        """ 檢查是不是imdb上找不到的電影

        :param imdbid:
        :return:
        """
        conn = psycopg2.connect(host=self.HOST, database=self.DB, user=self.USERNAME)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            select count(*) from movie_err_imdb where imdbid = '%s' and count > 5
            """ % imdbid)
            result = cursor.fetchone()
            return True if result[0] == 1 else False
        finally:
            cursor.close()
            conn.close()
