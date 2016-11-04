# -*- coding: utf-8 -*-


class IFilepath(object):
    """ 取得檔案位置

    """

    def get_filepath(self, filename):
        raise NotImplementedError


class NoSubdirFilepath(IFilepath):
    """ 沒有子目錄，檔名即Filepath

    """

    def get_filepath(self, filename):
        return filename


class SubdirNameBySuffixFilepath(IFilepath):
    """ 根據檔名的字尾長度決定子目錄的命名

    也就是希望子目錄裡的檔案有多少數量，如果希望子目錄裡有999個檔案，則保留3個字尾字元，取其前面的字元做子目錄名稱。
    例: 27862.html 取27為子目錄名稱; 另外27.html，因為不滿3個字元，則取27為子目錄名稱。

    """

    def __init__(self, suffix_num=3):
        self._suffix_num = suffix_num

    @property
    def suffix_num(self):
        return self._suffix_num

    def get_sbudir_name(self, filename):
        return filename[:len(filename) - self.suffix_num] if len(filename) > self.suffix_num else filename[:1]

    def get_filepath(self, filename):
        return '%s/%s' % (self.get_sbudir_name(filename), filename)


class SubdirNameByPrefixFilepath(IFilepath):
    """ 根據檔名的字首決字子目錄的命名

    """

    def __init__(self, prefix_num=3):
        self._prefix_num = prefix_num

    @property
    def prefix_num(self):
        return self._prefix_num

    def get_sbudir_name(self, filename):
        return filename[0:self.prefix_num] if len(filename) > self.prefix_num else filename[0:len(filename)]

    def get_filepath(self, filename):
        return '%s/%s' % (self.get_sbudir_name(filename), filename)
