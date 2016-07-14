# -*- coding: utf-8 -*-

# std
import subprocess
import sys
import os

# project
from lib.log import logger


class DbBackup(object):

    def __init__(self, host, usrname):
        self.HOST = host
        self.USERNAME = usrname
        self.Workdir_path = None

    def get_workdir_path(self):
        """ 取得工作目錄

        :return:
        """
        return self.Workdir_path

    def set_workdir_path(self, workdir_path):
        """ 設定工作目錄

        :param workdir_path:
        :return:
        """
        self.Workdir_path = workdir_path

    def get_backup_dir_path(self):
        return '%s/backup' % self.get_workdir_path()

    def dropdb(self, dbname):
        """ 刪除db

        :param dbname:
        :return:
        """
        cmd = "psql -h %s -U %s -c 'drop database if exists \"%s\"'" % (self.HOST, self.USERNAME, dbname)
        subprocess.check_call(cmd, shell=True)

    def createdb(self, dbname):
        """ 建立db

        :param dbname:
        :return:
        """
        self.dropdb(dbname)
        cmd = "createdb -h %s -U %s %s" % (self.HOST, self.USERNAME, dbname)
        subprocess.check_call(cmd, shell=True)

    def get_default_bakfile_path(self, dbname):
        return '%s/%s.bak' % (self.get_workdir_path(), dbname)

    def backupdb(self, dbname):
        """ 備份db

        :param dbname:
        :return:
        """
        cmd = "pg_dump -h %s -U %s -d %s -E utf-8 -f %s" \
              % (self.HOST, self.USERNAME, dbname, self.get_default_bakfile_path(dbname))
        subprocess.check_call(cmd, shell=True)

    def restoredb(self, dbname, filepath=None):
        """ 還原db

        :param dbname:
        :param filepath:
        :return:
        """
        if filepath is None:
            raise Exception('backup file path is None')
            # filepath = self.get_default_bakfile_path(dbname)

        self.createdb(dbname)
        cmd = "psql -h %s -U %s -d %s -f %s" % (self.HOST, self.USERNAME, dbname, filepath)
        subprocess.check_call(cmd, shell=True)

    def test_backupfile(self, dbname):
        """ 測試備份檔案是否能順利還原

        :param dbname:
        :return:
        """
        new_dbname = 'test_%s' % dbname
        backupfile = self.get_default_bakfile_path(dbname)
        self.restoredb(new_dbname, backupfile)
        self.dropdb(new_dbname)

    def move_backupfile(self, dbname):
        """ 將備份的檔案搬到BACKUPDIR裡，同時最多只存一份備份檔

        :param dbname:
        :return:
        """
        # 備份檔目錄
        if not os.path.exists(self.get_backup_dir_path()):
            os.mkdir(self.get_backup_dir_path())

        newpath = '%s/%s.bak' % (self.get_backup_dir_path(), dbname)
        tmppath = '%s/%s.tmp' % (self.get_backup_dir_path(), dbname)

        # rename exist backup file
        if os.path.exists(newpath):
            # del tmp
            if os.path.exists(tmppath):
                os.remove(tmppath)
            # rename exist bak to tmp
            os.rename(newpath, tmppath)

        # move backup file to backup directory
        os.rename(self.get_default_bakfile_path(dbname), newpath)

        # del temp file
        if os.path.exists(tmppath):
            os.remove(tmppath)

    def backup(self, dbname):
        logger.info('backup db')
        self.backupdb(dbname)
        logger.info('backup db is success!')

        logger.info('test backup db file')
        sys.stdout.flush()
        self.test_backupfile(dbname)
        logger.info('test backupfile is success!')

        self.move_backupfile(dbname)
