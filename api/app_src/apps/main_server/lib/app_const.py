# -*-coding: utf-8 -*-
"""Application const variables.
"""
from os import path as _path


APP_PATH = '%s/..' % _path.dirname(_path.realpath(__file__))
TMP_PATH = '%s/tmp' % APP_PATH
FILE_CACHE_PATH = '%s/cache' % APP_PATH
