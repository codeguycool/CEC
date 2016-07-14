# std
import os
import sys
import unittest

# project
from settings import DIR_EDP, DIR_SCRAPY, DIR_UNITTEST_MYSCRAPY
sys.path.append(os.path.dirname(DIR_EDP))
sys.path.append(os.path.dirname(DIR_SCRAPY))

if __name__ == '__main__':
    allsuite = unittest.TestLoader().discover(DIR_UNITTEST_MYSCRAPY, top_level_dir=DIR_EDP)
    unittest.TextTestRunner().run(allsuite)
