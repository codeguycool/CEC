# -*- coding: utf-8 -*-

""" MyScrapy的進入點

options:
--spider: The spider which you want to run.
--page: The number of pages you want to crawl. Default is last page.

"""

# std
import argparse
import os
import sys

# 3rd
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# project
from settings import DIR_EDP, DIR_SCRAPY
sys.path.append(os.path.dirname(DIR_EDP))

# parse argument
parser = argparse.ArgumentParser()
parser.add_argument("--spider", help="The spider which you want to run.", required=True)
parser.add_argument("--page", help="The number of pages you want to crawl. Default is last page.")
args = parser.parse_args()

# chang work directory
os.chdir(DIR_SCRAPY)

# crawler process
process = CrawlerProcess(get_project_settings())

# daily crawler
if args.spider.lower() in ('bttt', 'kubo'):
    process.crawl(args.spider, args.page)
else:
    process.crawl(args.spider)
process.start()
