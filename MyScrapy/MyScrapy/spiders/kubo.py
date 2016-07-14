# -*- coding: utf-8 -*-

# std
import logging
import re

# 3rd
import scrapy

# project
from MyScrapy.lib.searchdouban import SearchDouban, SearchParameters, DoubanApiStragety
from MyScrapy.parsers.douban import DoubanTvParser
from MyScrapy.parsers.imdb import ImdbTvParser
from MyScrapy.parsers.kubo import KuboTvParser


class KuboSpider(scrapy.Spider):
    name = 'kubo'
    allowed_domains = ['123kubo.com']
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.tv.TvPipeline': 300},
        'DOWNLOAD_DELAY': 5,
        'PROXY_ENABLED': False,
    }

    def __init__(self, page_limit=None):
        scrapy.Spider.__init__(self)
        self.page_limit = page_limit
        # self.proxy_scraper = FreeProxyScraper()

        # 更改spider name，以產生獨立的log
        if page_limit:
            self.name = 'kubo-daily'

    def parse(self, response):
        raise NotImplementedError

    # step1
    def start_requests(self):
        """ spider的啟始點

        爬取電視劇和動漫的第一頁

        :return:
        """
        baseurl_tv = 'http://www.123kubo.com/vod-search-id-2-cid-{0}-area--tag--year--wd--actor--order-vod_addtime%20desc-p-{1}.html'
        tv_types = ['16', '65', '15', '17', '18', '66', '19', '6']
        for tvtype in tv_types:
            yield scrapy.Request(baseurl_tv.format(tvtype, 1), callback=self.parse_pages, meta={'baseurl': baseurl_tv.format(tvtype, '{0}')})

        baseurl_anima = 'http://www.123kubo.com/vod-search-id-3-cid--area--tag--year--wd--actor--order-vod_addtime%20desc-p-{0}.html'
        yield scrapy.Request(baseurl_anima.format(1), callback=self.parse_pages, meta={'baseurl': baseurl_anima})

    # step2
    def parse_pages(self, response):
        """ 爬取列表

        :param response:
        :return:
        """
        baseurl = response.meta.get('baseurl')
        for pagecount in xrange(1, self.get_pagelimit(response) + 1):
            nextpage = baseurl.format(pagecount)
            yield scrapy.Request(nextpage, callback=self.parse_item, dont_filter=True)

    def get_pagelimit(self, response):
        """ 爬取的頁數

        :param response:
        :return:
        """
        if self.page_limit:  # 如果有指定爬取的頁數
            return int(self.page_limit)
        else:  # 沒有則爬到最後一頁
            pager = response.xpath("string(//div[@class='page clear']/p)").extract()[0]
            result = re.search(u'.*\d/(\d*)頁', pager)
            return int(result.groups(1)[0]) if result else 0

    # step3
    def parse_item(self, response):
        """ 取得列表上的item

        :param response:
        :return:
        """
        for li in response.xpath("//div[@class='listlf']/ul/li"):
            url = response.urljoin(li.xpath("./p[@class='t']/a/@href")[0].extract())
            kbparser = KuboTvParser(url)
            kbparser.parse()
            kbitem = kbparser.item

            if not kbitem:
                continue

            # 如果沒有播放來源則不處理
            if kbitem['play_urls'] == '{}':
                logging.info('%s no play_urls' % url)
                continue

            dbitem = self.get_douban_item(kbitem)
            imitem = self.get_imdb_item(dbitem)

            yield kbitem
            yield dbitem
            yield imitem

    def get_douban_item(self, kubo_item):
        """ 取得豆瓣的item

        :param kubo_item:
        :return:
        """
        if kubo_item is None:
            return

        kubo_item['dbid'] = None
        dbid = self.get_dbid(kubo_item)
        if dbid is not None:
            dbparser = DoubanTvParser('https://movie.douban.com/subject/%s/' % dbid, kubo_item['kind'])
            dbparser.parse()
            dbitem = dbparser.item
            if dbitem is None:
                return
            if dbitem['year'] != kubo_item['year']:
                return
            kubo_item['dbid'] = dbid
            dbitem.copy_from(kubo_item)
            return dbitem

    def get_dbid(self, kubo_item):
        """ 取得豆瓣ID

        利用title, star, year等資訊組成keyword，再利用google找出符合的豆瓣資料

        :param kubo_item:
        :return:
        """

        strategy = DoubanApiStragety()
        params = SearchParameters()
        search_obj = SearchDouban(strategy, params)
        dbid = search_obj.search(kubo_item)
        return dbid

    def get_imdb_item(self, douban_item):
        """ 取得imdb的item

        :param douban_item:
        :return:
        """
        if douban_item is not None and douban_item['imdbid'] is not None:
            imparser = ImdbTvParser(douban_item['imdbid'], douban_item['kind'])
            imitem = imparser.item
            imitem.copy_from(douban_item)
            return imitem
