# -*- coding: utf-8 -*-

""" 開眼電影的網路爬蟲

"""

# std
import datetime

# 3rd
import scrapy

# project
from lib.utils import parse_urlparams
from MyScrapy.parsers.atmovies import AtmoviesParser


class AtMoviesSpider(scrapy.Spider):
    name = 'atmovies'
    allowed_domains = ['gallery.photowant.com', 'atmovies.com.tw']
    # 利用圖王的年份分類做為爬蟲的起始點
    start_urls = [
        'http://gallery.photowant.com/B/gallery.cfm?action=year&y=%d' % y
        for y in xrange(datetime.datetime.now().year, 1960, -1)
    ]
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.movie.MoviePipeline': 200},
        'ROBOTSTXT_OBEY': False
    }

    # step1, 找出該年份電影的所有分頁
    def parse(self, response):
        """ spider的主要進入點

        :param response:
        :return:
        """
        last_page = AtMoviesSpider.get_last_page(response)
        for page in xrange(1, last_page + 1):
            url = "%s&page=%d" % (response.url, page)
            yield scrapy.Request(url, callback=self.parse_movie_on_page, dont_filter=True)

    @classmethod
    def get_last_page(cls, response):
        """ 取得各個年份的總頁數

        :param response:
        :return:
        """
        last_page = 0
        last_page_element = response.xpath("//td[@class='page11'][last()]/font/a/@href")
        if last_page_element:
            last_page_url = last_page_element[0].extract()
            params = parse_urlparams(last_page_url)
            if params['page']:
                last_page = int(params['page'][0])
        return last_page

    # step2, 找出該分頁中所有電影
    def parse_movie_on_page(self, response):
        """ 透過年份分類目次，取得filmid，並繼續取出電影資訊

        :param response:
        :return:
        """
        movies = response.xpath("//ul[@class='at15']/li")
        for movie_element in movies:
            try:
                movie_url = movie_element.xpath('./font/a[1]/@href')[0].extract()
                filmid = AtMoviesSpider.get_filmid(movie_url)
                atmovies_movie_url = "http://app2.atmovies.com.tw/film/%s/" % filmid

                # step3, parse item
                parser = AtmoviesParser(atmovies_movie_url)
                parser.parse()
                if parser.item is None:
                    pass
                else:
                    yield parser.item
            except IndexError:
                continue

    @classmethod
    def get_filmid(cls, url):
        """ 透過分析參數，取出filmid

        :param url:
        :return:
        """
        params = parse_urlparams(url)
        if params['filmid']:
            return params['filmid'][0].lower()
