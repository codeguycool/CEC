# -*- coding: utf-8 -*-

# std
import logging
import os
import time
import shutil
import urlparse

# 3rd
import requests

# project
from pathstrategy import NoSubdirFilepath, SubdirNameBySuffixFilepath
from MyScrapy.settings import DIR_SCRAPY_CACHE


class HtmlCache(object):
    """ Cache Html的類別，包含要儲存的位置，是否要重新下載...等

    """

    def __init__(self, url, url_id, expiredays=7,
                 old_filepath_inst=NoSubdirFilepath(),
                 filepath_inst=SubdirNameBySuffixFilepath(suffix_num=3),
                 *args, **kwargs):
        self.url = url
        self.url_id = url_id
        self.expiredays = expiredays
        self.filepath_instance = filepath_inst
        self.old_filepath_instance = old_filepath_inst

        self.init_dir()
        self.move_oldfile()
        self.remove_olddir()
        self.save(url, **kwargs)

    @property
    def filepath(self):
        return '%s/%s.html' % (self.get_cache_dir_path(), self.filepath_instance.get_filepath(self.url_id))

    @property
    def old_filepath(self):
        """ 儲存之前的檔案位置，用來將舊檔案搬移到新位置之用，若沒有逾期則可以省下下載的動作

        :return:
        """
        return '%s/%s.html' % (self.get_cache_dir_path(), self.old_filepath_instance.get_filepath(self.url_id))

    @property
    def html(self):
        if not os.path.exists(self.filepath):
            return ''

        with open(self.filepath, mode='r') as f:
            body = f.read()
            return body

    def get_cache_dir_path(self):
        """ 透過settings中的DIR_SCRAPY_CACHE，再加上網址的HOST做為cache_dir_path

        :return:
        """
        return '%s/%s' % (DIR_SCRAPY_CACHE, self.get_cache_dir_name())

    def get_cache_dir_name(self):
        return urlparse.urlparse(self.url).netloc

    def init_dir(self):
        if not os.path.exists(os.path.dirname(self.filepath)):
            os.makedirs(os.path.dirname(self.filepath))

    def move_oldfile(self):
        if os.path.exists(self.old_filepath):
            os.rename(self.old_filepath, self.filepath)

    def remove_olddir(self):
        old_dir_path = os.path.dirname(self.old_filepath)
        # 判斷是否為空目錄
        if os.path.exists(old_dir_path) and not os.listdir(old_dir_path):
            shutil.rmtree(old_dir_path)

    def save(self, url, force=False, **kwargs):
        """ 儲存頁面

        :param url:
        :param force:
        :param kwargs:
        :return:
        """
        if not self.should_be_download():
            return

        try:
            response = requests.get(url, timeout=30, **kwargs)
            if response.status_code == 200:
                write_mode = 'w+' if force else 'w'
                with open(self.filepath, mode=write_mode) as f:
                    f.writelines(response.content)
            else:
                logging.warning('url: %s, http status: %d' % (url, response.status_code))
        except requests.exceptions.Timeout:
            logging.warning('url: %s, timeout' % url)

    def should_be_download(self):
        """ 需不需要下載?

        如果檔案存在且沒過期就下載

        :return:
        """
        if os.path.exists(self.filepath) and not self.is_page_expire():
            return False
        else:
            return True

    def is_page_expire(self):
        """ 是否過期

        :return:
        """
        # 如果檔案不存在
        if not os.path.exists(self.filepath):
            return False
        else:
            now = time.time()
            timestamp = now - 60 * 60 * 24 * self.expiredays
            return True if timestamp > os.path.getctime(self.filepath) else False
