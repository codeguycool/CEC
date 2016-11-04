# -*-coding: utf-8 -*-
"""Application variables.
"""
# std lib
import os

# Directory Path
cur_path = os.path.dirname(os.path.realpath(__file__))
DIR_PROJECT_PATH = os.path.normpath('%s/../' % cur_path)
DIR_TEMP_PATH = '%s/tmp' % DIR_PROJECT_PATH
