# -*- coding: utf-8 -*-

# std
import re
import time

# project
from imdbpy import IMDbPy
from lib.log import logger


class LMDbManager(object):

    def __init__(self, db_operator):
        self.DbOperator = db_operator
        self.IMDbObj = IMDbPy()

    def import_imdbid(self, csvpath):
        """ 匯入imdbid

        :param csvpath:
        :return:
        """
        self.DbOperator.import_imdbid(csvpath)

    def _update_imdb_movies(self, getdata_func):
        """ 更新imdb電影資訊

        利用imdbpy去取得最新的電影資訊，然後更新資料庫

        :param getdata_func: 取得要更新的imdb電影
        :return:
        """
        i = 0
        since = 0
        while True:
            movies = getdata_func(limit=self.DbOperator.LIMIT, since=since)
            if movies:
                for movie in movies:
                    imdbid = movie[0]
                    try:
                        # 檢查是否正確的imdbid格式
                        if not re.match('tt\d{7}', imdbid):
                            raise Exception('not a valid imdbid')
                        if self.DbOperator.is_error_imdbid_movie(imdbid):
                            logger.info('error imdbid: %s' % imdbid)
                            continue
                        imdbmovie = self.IMDbObj.get_movie(imdbid)
                        imdbmovie.save2db(self.DbOperator.HOST, self.DbOperator.DB)
                        i += 1
                        logger.info(
                            (i, imdbid, imdbmovie['url'], imdbmovie['rating'], imdbmovie['posterurl']).__str__()
                        )
                    except Exception as e:
                        time.sleep(30)
                        # 如果imdb網路正常，卻取不到資訊，代表可能是錯誤的imdbid，所以要清除imdbid
                        if self.IMDbObj.is_network_ok():
                            self.DbOperator.clear_imdbid(imdbid)
                            logger.info('clear imdbid: %s' % imdbid)
                        else:
                            logger.warning('update imdb fail: %s' % (str(e)))
                            return

                since += self.DbOperator.LIMIT
                logger.info('exported count: %d' % i)
            else:
                break

    def update_imdb_miss_movies(self):
        """ 更新lmdb中其他來源(開眼、豆瓣…)有，但是imdb來源卻沒有找到的電影

        利用其他來源資料裡的imdbid，然後再用imdbpy取得電影資訊

        :return:
        """
        self._update_imdb_movies(self.DbOperator.get_imdb_miss_movies)

    def update_imdb_parsed_movies(self):
        """ 更新由imdb網站parse的電影

        lmdb中的imdb來源資料分2種，一種是由imdb plain text data file中取得的資料，另一種是透過imdbpy parse imdb取得的資料，
        若不持續的parse imdb，這些資料就無法被更新。

        :return:
        """
        self._update_imdb_movies(self.DbOperator.get_movies_for_imdb_reparse)