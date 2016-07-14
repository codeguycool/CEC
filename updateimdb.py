# -*- coding: utf-8 -*-

""" 將imdb資料匯入到lmdb資料庫

1. 下載imdb文字資料檔
2. 將imdb文字資料檔匯入成imdb資料庫
3. 利用imdbpy更新imdbid(去imdb網站搜尋找到只有一筆資料，或是名稱以及年份完全相同的電影)
4. 移除有重複imdbid(有可能造成錯誤)的電影
5. 將有imdbid的資料匯入到lmdb
6. 找出其他來源有而imdb資料裡沒有(找不到imdbid)的電影，利用imdbpy去抓取資訊
7. 重新抓取利用imdbpy抓取的電影，因為資料不是由imdb文字資料檔取得，若不重抓就無法更新

"""

# std
import datetime
import os
import subprocess
import sys
import traceback
from email.mime.text import MIMEText
from logging import DEBUG, INFO, FileHandler, basicConfig

# project
from settings import DIR_EDP, DIR_SCRAPY
sys.path.append(os.path.dirname(DIR_EDP))
sys.path.append(os.path.dirname(DIR_SCRAPY))

from MyCrontab.updateimdb.db_backup import DbBackup
from MyCrontab.updateimdb.db_operator import IMDBOperator
from MyCrontab.updateimdb.db_operator import LMDBOperator
from MyCrontab.updateimdb.downloader import CurlDownloader
from MyCrontab.updateimdb.imdb_manager import IMDbManager
from MyCrontab.updateimdb.lmdb_manager import LMDbManager
from lib.log import logger
from settings import *


def sendmail(body, subject='Import IMDB database fail!!!'):
    try:
        msg = MIMEText(body)
        msg["From"] = SENDER
        msg["To"] = RECEIVER
        msg["Subject"] = subject
        p = subprocess.Popen(["sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
        p.communicate(msg.as_string())
    except Exception:
        print traceback.format_exc()

if __name__ == '__main__':
    try:
        # logging
        basicConfig(level=INFO)
        file_handler = FileHandler('%s/update_imdb_in_lmdb.log' % DIR_IMDB_LOG, mode='w')
        file_handler.setLevel(DEBUG)
        logger.root.addHandler(file_handler)

        os.chdir(os.path.dirname(os.path.realpath(__file__)))

        os.environ["PATH"] += os.pathsep + POSTGRESQL_BIN_PATH
        os.environ["PATH"] += os.pathsep + USR_LOCAL_BIN_PATH
        os.environ["PATH"] += os.pathsep + USR_SBIN_PATH

        st = datetime.datetime.now()

        downloader = CurlDownloader(FTPHOST, FTPDIR, exclude_list=EXCLUDE_LIST)
        imdb_operator = IMDBOperator(IMDB_DB_HOST, IMDB_DB_NAME, IMDB_DB_ACCOUNT)
        lmdb_operator = LMDBOperator(LMDB_DB_HOST, LMDB_DB_NAME, LMDB_DB_ACCOUNT)
        db_backup = DbBackup(IMDB_DB_HOST, IMDB_DB_ACCOUNT)

        imdb_manager = IMDbManager(downloader, imdb_operator, db_backup, DIR_IMDB_TEMP)
        lmdb_manager = LMDbManager(lmdb_operator)

        # imdb
        # 下載imdb資料檔
        imdb_manager.download_listfile()
        # 匯入imdb資料檔
        imdb_manager.import_listfile()
        # 更新imdbidb
        imdb_manager.update_movie_imdbid()
        # 移除有重複imdbid的資料
        imdb_manager.remove_duplicate_imdb()
        # 備份
        imdb_manager.backup()
        # 匯出資料庫到lmdb
        imdb_manager.export2lmdb(lmdb_operator.HOST, lmdb_operator.DB)
        # 將imdbid匯出成csv
        imdbcsv_path = imdb_manager.imdbid2csv()

        # lmdb
        # 將imdbid匯入到lmdb
        lmdb_manager.import_imdbid(imdbcsv_path)
        # 更新lmdb中其他來源(開眼、豆瓣…)有，但是imdb來源卻沒有找到的電影
        lmdb_manager.update_imdb_miss_movies()
        # 更新由imdb網站parse的電影
        lmdb_manager.update_imdb_parsed_movies()

        # fixme
        """
        目前的方法是相信imdbpy取得的imdbid是正確的，並且以imdb資料庫的資料為主，若沒有才去imdb網站抓
        若imdbpy取得的imdbid錯誤，則會一直無法更正，要如何自動進行更新？
        """

        ed = datetime.datetime.now()

        message = 'start:%s \t end:%s' % (st, ed)
        logger.info(message)
    except Exception:
        print traceback.format_exc()
        sendmail(traceback.format_exc())
