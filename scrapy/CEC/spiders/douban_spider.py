# -*- coding: utf-8 -*-

""" 豆瓣電影的網路爬蟲

"""

# std lib
import datetime
import os
import re
import sys
import traceback

# 3rd lib
import scrapy
import scrapy.log
from scrapy.selector import Selector

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj lib
import CEC.items.movies_item
import CEC.settings
from CEC.spiders import savecache, is_page_exist, is_page_expire, get_body


def get_movieid(url):
    """ 取得豆瓣的movieid

    :param url:
    :return:
    """
    pattern = 'http:\/\/movie\.douban\.com\/subject\/(.+)\/'
    result = re.search(pattern, url)
    if result:
        return result.group(1)


def split_names(reviewed, index):
    """ 將豆瓣的title拆成主標題跟副標題，例：诺亚方舟漂流记 Ooops! Die Arche ist weg...
        利用html的title(诺亚方舟漂流记 (豆瓣))做為拆標題的依據。

    :param reviewed:
    :param index:
    :return:
    """
    title = reviewed[:index + -1].strip()
    subtitle = reviewed[index:].strip()
    return title, subtitle


def get_releaseDt(dtList):
    """  將上映日期的資訊轉成json格式

    e.g. 2015-08-15(台湾)、2015-07-30、1942-08-04（美国）
    :param dtList:
    :return:
    """
    dtDict = {}
    for dt in dtList:
        # find key position
        st = dt.find('(')
        ed = dt.find(')')
        if st == -1:
            st = dt.find('-')
            if st == 4:
                return {'Default': dt.strip(), u'全球': dt.strip()}
            return {}
        key = dt[st + 1:ed].strip()
        value = dt[:st]
        # value = value.replace(u'年', '-')
        # value = value.replace(u'月', '-')
        # value = value.replace(u'日', '-')
        dtDict[key] = value.strip()
    if len(dtDict) > 0:
        dtDict['Default'] = dtDict.values()[0]
    return dtDict


class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['douban.com']
    start_urls = ['http://movie.douban.com/tag/%s?type=R' % str(year) for year in xrange(1900, datetime.datetime.now().year + 1)]
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.movies_pipeline.MoviesPipeline': 300}
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
                link = response.url + "?type=R&start=" + str(i * 20)
                yield scrapy.Request(link, callback=self.parse_movielist)
        except IndexError:
            self.logger.info('%s page is empty' % response.url)
        except:
            self.logger.error(traceback.format_exc())

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
                vid = get_movieid(link)
                if not vid:
                    break

                # 如果已經有頁庫存檔，並且沒有過期，則執行step3
                if is_page_exist(self.name, vid) and not is_page_expire(self.name, vid, 30):
                    yield self.parse_movie(link, vid)
                else:
                    yield scrapy.Request(link, callback=self.cache_page, meta={'vid': vid})
        except:
            self.logger.error(traceback.format_exc())

    # step3, 頁庫存檔
    def cache_page(self, response):
        """ 處理電影的詳細內容, 先將網頁存成頁庫存檔，再呼叫get_item做處理

        :param response:
        :return:
        """
        if response.status == 200:
            savecache(self.name, response.meta['vid'], response.body)
            yield self.parse_movie(response.url, response.meta['vid'])

    # step4, 取得電影資訊
    def parse_movie(self, url, vid):
        """ 處理頁庫存檔，取出電影資訊

        :param url:
        :return:
        """
        item = CEC.items.movies_item.MoviesItem(CEC.items.movies_item.default_item)
        # fixme akas 有時候會不是空白的
        item['akas'] = []
        item['id'] = 'db_%s' % get_movieid(url)
        item['source'] = 'douban'
        item['url'] = url

        body = get_body(self.name, vid)
        sel = Selector(text=body)

        try:
            reviewded = sel.xpath("//div[@id='content']/h1/span[@property='v:itemreviewed']/text()")[0].extract()
            title = sel.xpath('//title/text()')[0].extract().strip()
            index = title.rfind(u'(豆瓣)')
            item['title'], item['subtitle'] = split_names(reviewded, index)
        except IndexError:
            pass

        convdict = {u"电影": 'movie', u"电视剧": 'tv'}

        try:
            item['kind'] = sel.xpath("//a[@data-url='http://movie.douban.com/subject/%s/']/@data-type" % vid)[0].extract()
            item['kind'] = convdict.get(item['kind'], item['kind'])
        except IndexError:
            pass

        try:
            item['rating'] = sel.xpath("//strong[@property='v:average']/text()")[0].extract()
        except IndexError:
            pass

        try:
            item['posterurl'] = sel.xpath("//img[@rel='v:image']/@src")[0].extract()
            if item['posterurl'].find('http://img6.douban.com/mpic/') > -1:
                item['posterurl'] \
                    = item['posterurl'].replace('http://img6.douban.com/mpic/', 'http://img6.douban.com/lpic/')
            elif item['posterurl'].find('http://img6.douban.com/view/movie_poster_cover/spst/public/') > -1:
                item['posterurl'] = \
                    item['posterurl'].replace('http://img6.douban.com/view/movie_poster_cover/spst/public/',
                                              'http://img6.douban.com/view/photo/photo/public/')
        except IndexError:
            pass

        try:
            item['directors'] = sel.xpath("//a[@rel='v:directedBy']/text()").extract()
            if not isinstance(item['directors'], list):
                item['directors'] = item['directors'].split('/')
            item['directors'] = [director.strip() for director in item['directors']]
        except IndexError:
            pass

        try:
            item['writers'] = sel.xpath(u"//div[@id='info']/span/span[text()='编剧']/following-sibling::span/a/text()").extract()
            if not isinstance(item['writers'], list):
                item['writers'] = item['writers'].split('/')
            item['writers'] = [writer.strip() for writer in item['writers']]
        except IndexError:
            pass

        try:
            item['stars'] = sel.xpath("//a[@rel='v:starring']/text()").extract()
            if not isinstance(item['stars'], list):
                item['stars'] = item['stars'].split('/')
            item['stars'] = [start.strip() for start in item['stars']]
        except IndexError:
            pass

        try:
            item['genres'] = sel.xpath("//div[@id='info']/span[@property='v:genre']/text()").extract()
        except IndexError:
            pass

        try:
            item['year'] = sel.xpath("//div[@id='content']/h1/span[@class='year']/text()")[0].extract().strip()
            item['year'] = item['year'][1:5]
        except IndexError:
            pass

        try:
            item['countries'] = sel.xpath(u"//div[@id='info']/span[text()='制片国家/地区:']/following-sibling::text()[1]")[0].extract().strip()
            item['countries'] = [country.strip() for country in item['countries'].split('/')]
        except IndexError:
            pass

        try:
            item['languages'] = sel.xpath(u"//div[@id='info']/span[text()='语言:']/following-sibling::text()[1]")[0].extract().strip()
            item['languages'] = [lang.strip() for lang in item['languages'].split('/')]
        except IndexError:
            pass

        try:
            item['releaseDate'] = sel.xpath("//div[@id='info']/span[@property='v:initialReleaseDate']/@content").extract()
            item['releaseDate'] = {} if item['releaseDate'] == [] else item['releaseDate']
            item['releaseDate'] = get_releaseDt(item['releaseDate'])
        except IndexError:
            pass

        try:
            item['runtimes'] = sel.xpath("//div[@id='info']/span[@property='v:runtime']/@content")[0].extract()
        except IndexError:
            pass

        try:
            item['akas'] = sel.xpath(u"//div[@id='info']/span[text()='又名:']/following-sibling::text()")[0].extract()
            item['akas'] = [name.strip() for name in item['akas'].split('/')]
        except IndexError:
            pass

        if item['subtitle']:
            item['akas'].append(item['subtitle'])

        try:
            item['description'] = sel.xpath("normalize-space(string(//span[@property='v:summary']))")[0].extract().strip()
            if item['description'] == '': item['description'] = None
        except IndexError:
            pass

        try:
            item['imdbid'] = sel.xpath(u"//div[@id='info']/span[text()='IMDb链接:']/following-sibling::a/text()")[0].extract()
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
    process.crawl(DoubanSpider)
    process.start()