# -*- coding: utf-8 -*-

# std
import os
import shutil
import subprocess
import time
import traceback

# project
from imdbpy import IMDbPy
from lib.log import logger
from settings import DIR_CRONTAB


class IMDbManager(object):

    def __init__(self, downloader, db_operator, db_backup, workdir_path):
        if workdir_path is None:
            raise Exception("workdir path is None")

        self.Downloader = downloader
        self.DbOperator = db_operator
        self.DbBackup = db_backup
        self.IMDbObj = IMDbPy(self.DbOperator.URI)
        self.Workdir_path = workdir_path

        # 修改工作目錄
        self.Downloader.set_download_dir_path('%s/list' % workdir_path)
        self.DbBackup.set_workdir_path(workdir_path)

    def download_listfile(self):
        """ 下載IMDB的資料庫文字檔，http://www.imdb.com/interfaces

        :return:
        """
        logger.info('download listfile')
        self.Downloader.download()
        logger.info('download listfile is success!')

    def get_csvdir(self):
        """ 取得csv目錄

        :return:
        """
        return '%s/csvdir' % self.Workdir_path

    def make_csvdir(self):
        """ 建立csv目錄

        :return:
        """
        if os.path.exists(self.get_csvdir()):
            shutil.rmtree(self.get_csvdir())
        os.mkdir(self.get_csvdir())

        # fixme: 修改成不需更改csv目錄的權限的方法
        os.chmod(self.get_csvdir(), 0747)

    def import_listfile(self):
        """ 將IMDB的資料庫文字檔匯進DB

        如果匯入時發生問題，則利用上次的備份檔進行還原

        :return:
        """
        logger.info('import listfile to db')

        try:
            self.make_csvdir()
            imdbpy2sql_path = os.path.normpath('%s/updateimdb/bin/' % DIR_CRONTAB)
            cmd = 'python %s/imdbpy2sql.py -d %s -u %s -c %s -i table' \
                  % (imdbpy2sql_path, self.Downloader.get_download_dir_path(), self.DbOperator.URI, self.get_csvdir())
            subprocess.check_call(cmd, shell=True)
        except Exception:
            logger.error('error occurred during import listfile to db, try to restore the older db')
            self.DbBackup.restoredb(self.DbOperator.DB, '%s/%s.bak' % (self.DbBackup.BACKUPDIR, self.DbOperator.DB))
            logger.info('restore success!')
            raise

        logger.info('import listfile to db is success!')

    def update_movie_imdbid(self):
        """ 更新IMDB資料庫電影的IMDBID

        如果更新某部電影的IMDBID，出現錯誤連續達到10次，則不繼續嘗試更新IMDBID（可能會是網路等問題）

        :return:
        """

        logger.info('update imdb_id field')

        count = 0
        max_try = 10

        while True:
            movies = self.DbOperator.get_null_imdbid_movies()
            if len(movies) == 0:
                break

            for movie in movies:
                try_times = 0
                count += 1

                try:
                    logger.info('%s: %s' % (count, self.get_imdbid_result(movie[0])))
                except Exception:
                    try_times += 1
                    time.sleep(3)
                    if try_times == max_try:
                        logger.error(traceback.format_exc())
                        return

        logger.info('import db to table is success!')

    def get_imdbid_result(self, movieid):
        """ 找出movie的imdbid

        :param movieid:
        :return:
        """
        imdbid_for_imdbpy = self.IMDbObj.get_imdbid(movieid)
        if imdbid_for_imdbpy:
            imdbid = 'tt%07d' % int(imdbid_for_imdbpy)
            return '%s is ok! imdbid:%s' % (movieid, imdbid)
        else:
            self.DbOperator.set_imdbid_as_zero(movieid)
            return "%s can't find imdbid" % movieid

    def remove_duplicate_imdb(self):
        """ 移除有重複imdbid的資料

        :return:
        """
        self.DbOperator.remove_duplicate_imdb()

    def backup(self):
        """ 備份資料庫

        :return:
        """
        self.DbBackup.backup(self.DbOperator.DB)

    def export2lmdb(self, lmdb_host, lmdb_dbname):
        """ 匯出IMDB資料庫的資料到LMDB

        :param lmdb_host:
        :param lmdb_dbname:
        :return:
        """

        logger.info('export to lmdb')

        since = 0
        i = 0

        while True:
            movies = self.DbOperator.get_movies_to_export_lmdb(since, limit=self.DbOperator.LIMIT)
            if movies:
                for movie in movies:
                    movieid = movie[0]
                    imdbid = 'tt%07d' % int(movie[1])
                    i += 1
                    try:
                        imdbmovie = self.IMDbObj.get_movie(imdbid, movieid)
                        imdbmovie.save2db(lmdb_host, lmdb_dbname)
                        logger.info(
                            '%d, %s, %s, %s, %s' % (i, movieid, imdbid, imdbmovie['url'], imdbmovie['posterurl'])
                        )
                    except Exception as e:
                        logger.error('save db error: %s \r\n %s' % (imdbid, str(e)))

                since += self.DbOperator.LIMIT
            else:
                break

    def imdbid2csv(self):
        """ 匯出imdbid到csv

        :return:
        """
        csv_path = '%s/imdbid.csv' % self.Workdir_path
        self.DbOperator.imdbid2csv(csv_path)
        return csv_path
