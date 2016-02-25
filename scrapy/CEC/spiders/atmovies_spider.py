# -*- coding: utf-8 -*-

""" 開眼電影的網路爬蟲

"""

# std lib
import datetime
import hashlib
import json
import os
import sys
import urlparse
import urllib2

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


class AtMoviesSpider(scrapy.Spider):
    name = 'atmovies'
    allowed_domains = ['gallery.photowant.com', 'atmovies.com.tw']
    start_urls = ['http://gallery.photowant.com/B/gallery.cfm?action=year&y=%d' % y for y in xrange(1960, datetime.datetime.now().year + 1)]
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.movies_pipeline.MoviesPipeline': 300}
    }

    def _get_last_page(self, response):
        """ 取得各個年份的總頁數

        :param response:
        :return:
        """
        last_page = 0
        last_page_url = response.xpath("//td[@class='page11'][last()]/font/a/@href")
        if last_page_url:
            last_page_url = last_page_url[0].extract()
            parsed_url = urlparse.urlparse(last_page_url)
            params = urlparse.parse_qs(parsed_url.query)
            if params['page']:
                last_page = int(params['page'][0])
        return last_page

    # step1, 找出該年份電影的所有分頁
    def parse(self, response):
        """ spider的主要進入點

        :param response:
        :return:
        """
        last_page = self._get_last_page(response)
        for page in xrange(1, last_page + 1):
            url = response.urljoin(response.url)
            url = "%s&page=%d" % (url, page)
            yield scrapy.Request(url, callback=self.parse_movielist)

    def _get_filmid(self, url):
        """ 透過分析參數，取出filmid

        :param url:
        :return:
        """
        parsed_url = urlparse.urlparse(url)
        params = urlparse.parse_qs(parsed_url.query)
        if params['filmid']:
            return params['filmid'][0].lower()

    # step2, 找出該分頁中所有電影
    def parse_movielist(self, response):
        """ 透過年份分類目次，取得filmid，並繼續取出電影資訊

        :param response:
        :return:
        """
        films = response.xpath("//ul[@class='at15']/li")
        for film in films:
            # 找電影的url
            url = None
            try:
                url = film.xpath('./font/a[1]/@href')[0].extract()
            except IndexError:
                continue

            filmid = self._get_filmid(url)
            # 取不到filmid
            if not filmid:
                continue

            if is_page_exist(self.name, filmid) and not is_page_expire(self.name, filmid, 30):
                yield self.parse_movie(filmid)
            else:
                # 如果沒有暫存檔或是已經過期，執行step3
                movieurl = "http://ww2.atmovies.com.tw/film/film.cfm?filmid=%s" % filmid
                yield scrapy.Request(movieurl, meta={'filmid': filmid}, callback=self.cache_page)

    # step3, 暫存頁面
    def cache_page(self, response):
        vid = response.meta['filmid']

        if response.status == 200:
            savecache(self.name, vid, response.body)
            yield self.parse_movie(vid)

    def _get_title(self, vid):
        """ 取得 title & subtitle

        :param vid:
        :return:
        """
        url = 'http://gallery.photowant.com/b/gallery.cfm?action=still&filmid=%s' % vid
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        html = response.read()
        sel = Selector(text=html)
        try:
            return sel.xpath("//font[@class='at15b']/text()").extract()
        except IndexError:
            pass

    def _get_date_runtime(self, element):
        date_runtime = {}
        key_dict = {
            u'片長': 'runtimes',
            u'上映日期': 'releaseDate',
        }
        for info in element:
            string = info.extract().strip().replace(u'分', '')
            token = string.split(u'：')
            if len(token) == 2:
                key = key_dict.get(token[0], token[0])
                value = token[1]
                date_runtime[key] = value

        return date_runtime

    def _get_cast(self, element):
        """ 取得導演、編劇、演員等資訊

        :param element:
        :return:
        """
        key = None
        info = {}
        key_dict = {
            u'導演：': 'directors',
            u'編劇：': 'writers',
            u'演員：': 'stars'
        }
        for li in element:
            try:
                key = li.xpath('./b/text()')[0].extract().strip()
                key = key_dict.get(key, key)
                info[key] = []
            except IndexError:
                pass

            if key:
                try:
                    name = li.xpath('./a/text()')[0].extract().strip()
                    if name:
                        info[key].append(name)
                except IndexError:
                    pass

        return info

    # step4, 取得電影資訊
    def parse_movie(self, vid):
        """ 取得電影資訊

        :param vid:
        :return:
        """
        item = CEC.items.movies_item.MoviesItem(CEC.items.movies_item.default_item)
        item['id'] = 'am_%s' % vid
        item['source'] = 'atmovies'
        item['kind'] = "movie"
        item['genres'] = []
        item['url'] = "http://ww2.atmovies.com.tw/film/film.cfm?filmid=%s" % vid

        body = get_body(self.name, vid)
        sel = Selector(text=body)

        title = self._get_title(vid)
        if title:
            item['title'] = title[0]
            item['akas'] = [title[1]] if len(title) == 2 else []

        try:
            item['runtimes'] = sel.xpath("//ul[@class='runtime']/li[1]/text()")[0].extract().strip().replace(u'片長：', '').replace(u'分', '')
        except IndexError:
            pass

        try:
            item['releaseDate'] = sel.xpath("//ul[@class='runtime']/li[2]/text()")[0].extract().strip().replace(u'上映日期：', '')
            item['releaseDate'] = {'Default': item['releaseDate'], 'TW': item['releaseDate']}
        except IndexError:
            pass

        date_runtime = self._get_date_runtime(sel.xpath("//ul[@class='runtime']/li/text()"))
        item['runtimes'] = date_runtime.get('runtimes')
        item['releaseDate'] = date_runtime.get('releaseDate', {})
        if item['releaseDate']:
            item['releaseDate'] = {'Default': item['releaseDate'], 'TW': item['releaseDate']}

        try:
            item['rating'] = sel.xpath("//div[@class='star']/table/tr/td/a/img/@width")[0].extract()
            item['rating'] = float(item['rating']) / 20
        except IndexError:
            pass

        try:
            item['posterurl'] = sel.xpath("//div[@id='movie_poster']/a/img/@src")[0].extract()
            if item['posterurl'] == "http://images.atmovies.com.tw/images/spacer.gif":
                item['posterurl'] = None
        except IndexError:
            pass

        cast = self._get_cast(sel.xpath("//div[@id='filmCastDataBlock']/ul[1]/li[position() < last()]"))
        if cast:
            item['directors'] = cast.get('directors', [])
            item['writers'] = cast.get('writers', [])
            item['stars'] = cast.get('stars', [])

        try:
            item['year'] = sel.xpath(u"//div[@id='filmCastDataBlock']/ul/li/b[text()='影片年份：']/following-sibling::text()[1]")[0].extract().strip()
            if item['year'] == '':
                item['year'] = None
        except IndexError:
            pass

        try:
            item['countries'] = sel.xpath(u"//div[@id='filmCastDataBlock']/ul/li/b[text()='出  品  國：']/following-sibling::text()[1]")[0].extract()
            item['countries'] = item['countries'].replace(u'、', ',')
            item['countries'] = item['countries'].replace(u'／', ',')
            item['countries'] = item['countries'].replace('/', ',')
            item['countries'] = item['countries'].replace('|', ',')
            item['countries'] = item['countries'].replace('&', ',')
            item['countries'] = filter(None, item['countries'].strip().split(','))
            item['countries'] = [country.strip() for country in item['countries']]
        except IndexError:
            pass

        try:
            item['languages'] = sel.xpath(u"//div[@id='filmCastDataBlock']/ul/li/b[text()='語　　言：']/following-sibling::text()[1]")[0].extract()
            item['languages'] = item['languages'].replace(u'、', ',')
            item['languages'] = item['languages'].replace(u'／', ',')
            item['languages'] = item['languages'].replace('/', ',')
            item['languages'] = item['languages'].replace('|', ',')
            item['languages'] = item['languages'].replace('&', ',')
            item['languages'] = filter(None, item['languages'].strip().split(','))
            item['languages'] = [lang.strip() for lang in item['languages']]
        except IndexError:
            pass

        try:
            item['description'] = sel.xpath("normalize-space(string(//img[@src='http://images.atmovies.com.tw/images/movie/ion_t02.gif']/..))")[0].extract().strip()
            if item['description'].find(u'劇情簡介') == 0:
                item['description'] = item['description'][4:]
        except IndexError:
            pass

        try:
            item['imdbid'] = sel.xpath("//div[@id='filmCastDataBlock']/ul/li/a[text()='IMDb']/@href")[0].extract()
            item['imdbid'] = item['imdbid'].replace('http://us.imdb.com/Title?', 'tt')
        except IndexError:
            pass

        item['md5sum'] = hashlib.md5(json.dumps(item.__dict__, sort_keys=True)).hexdigest()

        # 如果releaseDate為空，且year不為空，將year的值給releaseDate['Default']
        if not item['releaseDate'] and item['year'] is not None:
            item['releaseDate'] = {'Default': item['year']}

        if item['title'] is not None or item['akas']:
            return item

if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(AtMoviesSpider)
    process.start()