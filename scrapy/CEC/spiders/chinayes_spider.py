# -*- coding: utf-8 -*-

""" Yes電影的網路爬蟲

"""

# std lib
import os
import re
import sys

# 3rd lib
import scrapy
from scrapy.selector import Selector

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj lib
import CEC.items.movies_item
import CEC.settings
from CEC.spiders import savecache, is_page_exist, is_page_expire, get_body


class ChinaYesSpider(scrapy.Spider):
    name = 'chinayes'
    allowed_domains = ['tw.movie.chinayes.com']
    start_urls = ['http://tw.movie.chinayes.com/database/search']
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.movies_pipeline.MoviesPipeline': 300}
    }

    # step1, 找出所有電影，若該頁有下一頁則遞迴處理
    def parse(self, response):
        movies = response.xpath("//ul/li[@class='showBx']")
        for movie in movies:
            year = movie.xpath(u".//em[text()='影片年份：']/following-sibling::text()")[0].extract()
            titles = movie.xpath(".//h3[@class='subtitle']/a/em/text()").extract()
            url = response.urljoin(movie.xpath("./span[@class='imgBx fLt']/a/@href")[0].extract())
            rating = movie.xpath(".//li[@class='point']/text()")[0].extract()

            if year == u'未定': year = None
            filmid = url.split('/')[-1]

            if is_page_exist(self.name, filmid) and not is_page_expire(self.name, filmid, 30):
                yield self.parse_movie(filmid, year, titles, rating, url)
            else:
                # 如果沒有暫存頁面或是已經過期，執行step2
                yield scrapy.Request(url, meta={'filmid': filmid, 'year': year, 'titles': titles, 'rating': rating}, callback=self.cache_page)

        # next page
        nextpage = response.xpath("//a[text()='Next >']/@href")
        if nextpage:
            page = response.meta['page'] + 1 if 'page' in response.meta else 2
            url = 'http://tw.movie.chinayes.com/database/search/%d' % page
            yield scrapy.Request(url, callback=self.parse, meta={'page': page})

    # step2, 暫存頁面
    def cache_page(self, response):
        vid = response.meta['filmid']
        year = response.meta['year']
        titles = response.meta['titles']
        rating = response.meta['rating']

        if response.status == 200:
            savecache(self.name, vid, response.body)
            yield self.parse_movie(vid, year, titles, rating, response.url)

    # step3, 取得電影資訊
    def parse_movie(self, vid, year, titles, rating, url):
        item = CEC.items.movies_item.MoviesItem(CEC.items.movies_item.default_item)

        item['id'] = 'cy_%s' % vid
        item['source'] = 'chinayes'
        item['kind'] = "movie"
        item['url'] = url
        item['year'] = year
        item['rating'] = rating
        item['title'] = titles[0]
        item['akas'] = titles[1:]

        body = get_body(self.name, vid)
        sel = Selector(text=body)

        try:
            item['posterurl'] = sel.xpath(u"//span[@class='imgBx fLt']/img/@src")[0].extract().strip()
            if item['posterurl'] == "/images/posterBg.jpg": item['posterurl'] = None
        except IndexError:
            pass

        try:
            item['directors'] = sel.xpath(u"//p[@class='summary fLt']/em[text()='導演：']/../following-sibling::ul[1]/li/a/text()").extract()
        except IndexError:
            pass

        try:
            item['writers'] = sel.xpath(u"//p[@class='summary fLt']/em[text()='編劇：']/../following-sibling::ul[1]/li/a/text()").extract()
        except IndexError:
            pass

        try:
            item['stars'] = sel.xpath("//div[@class='actor']/span[@class='actor-item']/a/text()").extract()
        except IndexError:
            pass

        try:
            item['genres'] = sel.xpath(u"//p[@class='summary']/em[text()='類型：']/following-sibling::a/text()").extract()
        except IndexError:
            pass

        try:
            item['countries'] = sel.xpath(u"//p[@class='summary']/em[text()='出品國：']/following-sibling::text()")[0].extract()
            item['countries'] = filter(None, item['countries'].split(','))
            item['countries'] = [country.strip() for country in item['countries']]
        except IndexError:
            pass

        try:
            item['languages'] = sel.xpath(u"//p[@class='summary']/em[text()='語言：']/following-sibling::text()")[0].extract()
            item['languages'] = filter(None, item['languages'].split(','))
            item['languages'] = [lang.strip() for lang in item['languages']]
        except IndexError:
            pass

        try:
            item['runtimes'] = sel.xpath(u"//p[@class='summary']/em[text()='片長：']/following-sibling::text()")[0].extract().strip()
            result = re.search('(?:.*:)?([\d|\s]*)\(?', item['runtimes'])
            item['runtimes'] = result.group(1) if result and result.group() else None
        except IndexError:
            pass

        try:
            rdate_dict = {}
            for rdate in sel.xpath(u"//p[@class='summary fLt']/em[text()='上映日期：']/../following-sibling::ul/li/text()").extract():
                result = re.search('([^\(]*)\((.*)\)', rdate)
                if result and result.group(2):
                    rdate_dict[result.group(2)] = result.group(1).strip()
            if len(rdate_dict) > 0:
                rdate_dict['Default'] = rdate_dict.values()[0]
            item['releaseDate'] = rdate_dict
        except IndexError:
            pass

        try:
            item['imdbid'] = sel.xpath(u"//p[@class='summary']/em[text()='IMDb：']/following-sibling::a/text()")[0].extract().strip()
        except IndexError:
            pass

        try:
            item['description'] = sel.xpath(u"normalize-space(string(//span[text()='劇情簡介']/following-sibling::p))")[0].extract()
        except IndexError:
            pass

        # 如果releaseDate為空，且year不為空，將year的值給releaseDate['Default']
        if not item['releaseDate'] and item['year'] is not None:
            item['releaseDate'] = {'Default': item['year']}

        return item


if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(ChinaYesSpider)
    process.start()