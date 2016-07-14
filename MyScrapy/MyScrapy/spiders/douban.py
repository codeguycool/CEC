# -*- coding: utf-8 -*-

""" 豆瓣電影的網路爬蟲

"""

# std
import datetime
import logging
import traceback

# 3rd
import scrapy

# project
from MyScrapy.parsers.douban import DoubanMovieParser


class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['douban.com']
    start_urls = ['https://movie.douban.com/tag/%s?type=R' % str(year)
                  for year in xrange(datetime.datetime.now().year, 1950, -1)]
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.movie.MoviePipeline': 300},
        'DOWNLOAD_DELAY': 5
    }

    # step1, 找出該年份電影的所有分頁
    def parse(self, response):
        """ spider的主要進入點

        :param response:
        :return:
        """
        try:
            lastpage = response.xpath("//div[@class='paginator']/span[@class='thispage']/@data-total-page").extract()[0]
            lastpage = int(lastpage)
            for i in xrange(lastpage):
                link = response.url + "&start=" + str(i * 20)
                yield scrapy.Request(link, callback=self.parse_movielist)
        except IndexError:
            logging.info('%s page is empty' % response.url)

    # step2, 找出該分頁中所有電影的vid
    def parse_movielist(self, response):
        """ 處理分頁上的電影連結

        :param response:
        :return:
        """
        try:
            movies = response.xpath("//a[@class='nbg']/@href").extract()
            for movie in movies:
                link = response.urljoin(movie)

                parser = DoubanMovieParser(link)
                parser.parse()
                if not parser.item or parser.item['kind'] is None:
                    continue
                yield parser.item
        except:
            logging.error(traceback.format_exc())
