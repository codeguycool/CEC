# -*- coding: utf-8 -*-

# std
import ftplib
import os
import sys

# 3rd
import pycurl

# project
from lib.log import logger


class Downloader(object):

    def __init__(self, ftp_host, ftp_dir, exclude_list=None, maxtry=10):
        self.FtpHost = ftp_host
        self.FtpDir = ftp_dir
        self.ExcludeList = exclude_list
        self.MaxTry = maxtry
        self.Download_dir_path = None

    def get_download_dir_path(self):
        """ 取得下載目錄

        :return:
        """
        return self.Download_dir_path

    def set_download_dir_path(self, download_dir_path):
        """ 設定下載目錄

        :param download_dir_path:
        :return:
        """
        self.Download_dir_path = download_dir_path

    def get_ftp_file_uri(self, filename):
        """ ftp的檔案位置

        :param filename:
        :return:
        """
        return 'ftp://%s%s%s' % (self.FtpHost, self.FtpDir, filename)

    def get_local_file_path(self, filename):
        """ local的檔案位置

        :param filename:
        :return:
        """
        return '%s/%s' % (self.get_download_dir_path(), filename)

    def get_ftp_filesize(self, filename):
        """ 取得ftp上的檔案大小

        :param filename:
        :return:
        """
        raise NotImplementedError

    def down_ftp_file(self, filename):
        """ 下載ftp的檔案

        :param filename:
        :return:
        """
        raise NotImplementedError

    def is_downloaded(self, filename):
        """ 是否已經下載過了

        利用ftp的檔案大小跟local的檔案大小比較

        :param filename:
        :return:
        """
        # ftp的檔案大小
        ftp_file_size = self.get_ftp_filesize(filename)
        # local的檔案大小
        local_file_size = os.path.getsize(self.get_local_file_path(filename)) \
            if os.path.exists(self.get_local_file_path(filename)) else 0
        return True if ftp_file_size == local_file_size else False

    @classmethod
    def is_gzfile(cls, filename):
        """ 是否是.gz檔

        :param filename:
        :return:
        """
        token = os.path.splitext(filename)
        if token[1].lower() == '.gz':
            return True
        else:
            return False

    def is_allow_file(self, filename):
        """ 檢查檔案是否有列EXCLUDE_LIST裡

        :param filename:
        :return:
        """
        if self.ExcludeList is None:
            return True
        if self.ExcludeList and filename not in self.ExcludeList:
            return True
        return False

    def is_target_file(self, filename):
        """ 檢查是否要下載的檔案

        1. 是gz檔
        2. 沒有被列在檢查檔案是否有列EXCLUDE_LIST裡裡
        3. 沒有下載過

        :param filename:
        :return:
        """
        if Downloader.is_gzfile(filename) and self.is_allow_file(filename) and not self.is_downloaded(filename):
            return True
        else:
            return False

    def _download(self, filename):
        """ 下載檔案，並且最多可以嘗試MAXTRY次

        :param filename:
        :return:
        """
        max_try = self.MaxTry
        while True:
            try:
                logger.info('download %s' % self.get_ftp_file_uri(filename))
                sys.stdout.flush()
                self.down_ftp_file(filename)
                break
            except Exception as e:
                max_try -= 1
                if max_try >= 0:
                    logger.warning('retry: %s, msg: %s' % (filename, str(e)))
                else:
                    logger.error('download %s fail!' % filename)
                    raise

    def download(self):
        if self.get_download_dir_path() is None:
            raise Exception("Download dir path is None")

        # 建立下載目錄
        if not os.path.exists(self.get_download_dir_path()):
            os.mkdir(self.get_download_dir_path())

        # 登錄
        ftp = ftplib.FTP(host=self.FtpHost)
        ftp.login()
        ftp.cwd(self.FtpDir)

        # 取出檔案列表
        for filename in ftp.nlst():
            # 如果不是要下載的檔案
            if not self.is_target_file(filename):
                logger.info('skip: %s' % filename)
                continue
            # 下載
            self._download(filename)


class CurlDownloader(Downloader):
    """ 利用Curl進行下載

    """

    def __init__(self, ftphost, ftpdir, exclude_list=None, maxtry=10):
        Downloader.__init__(self, ftphost, ftpdir, exclude_list, maxtry)

    def get_ftp_filesize(self, filename):
        """ 取得ftp上的檔案大小

        :param filename:
        :return:
        """
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.get_ftp_file_uri(filename))
        c.setopt(c.NOBODY, 1)
        c.perform()
        size = int(c.getinfo(c.CONTENT_LENGTH_DOWNLOAD))
        c.close()
        return size

    def down_ftp_file(self, filename):
        """ 下載ftp的檔案

        :param filename:
        :return:
        """
        destination_file = open(self.get_local_file_path(filename), 'wb')
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.get_ftp_file_uri(filename))
        c.setopt(pycurl.WRITEDATA, destination_file)
        c.setopt(pycurl.NOPROGRESS, 0)
        c.perform()
        c.close()
