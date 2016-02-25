# std lib
import os
import sys

# 3rd lib
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(CUR_PATH))

# project lib
from CEC.settings import DIR_PROJ

os.chdir(DIR_PROJ)
crawlers = list()
process = CrawlerProcess(get_project_settings())
process.crawl('bttt')
process.crawl('atmovies')

#record crawlers.
for crawler in process.crawlers:
    crawlers.append(crawler)

process.start()
#FIXME, Is it need for join()?
process.join()

for crawler in crawlers:
    #FIXME.
    print crawler.stats.get_stats()