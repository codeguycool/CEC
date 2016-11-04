# -*- coding: utf-8 -*-

""" 土豆的網路爬蟲

"""

# std
import datetime
import hashlib
import json
import logging
import os

# 3rd
import lxml.html
import requests
import scrapy
from twisted.internet.error import TimeoutError

# project
from lib.utils import fix_response_encoding
import MyScrapy.items.movie_content


class TudouSpider(scrapy.Spider):
    """ Get Tudou All free movie content
    http://www.tudou.com/list/ach5a-2b-2c-2d-2e1309f998g-2h-2i-2j-2k-2l-2m-2n-2sort2.html

    """
    name = 'tudou'
    allowed_domains = ['tudou.com']
    baseurl = 'http://www.tudou.com/s3portal/service/pianku/data.action?pageSize=90&app=mainsitepc&deviceType=1&' \
              'tags=998&tagType=3&firstTagId=5&areaCode=710000&initials=&hotSingerId=&pageNo=%d&sortDesc=quality'
    start_urls = [baseurl % 1]
    custom_settings = {
        'ITEM_PIPELINES': {'MyScrapy.pipelines.movie_content.MovieContentPipeline': 300}
    }

    def parse(self, response):
        # get page count
        jsondata = json.loads(response.body)
        pagecount = int(jsondata['total']) / 90

        for i in xrange(1, pagecount + 1):
            yield scrapy.Request(self.baseurl % i, callback=self.parse_page, errback=self.err_back)

    def err_back(self, failure):
        if failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def parse_page(self, response):
        # 取得data資訊
        data = json.loads(response.body)
        # 取得album資訊
        albums = self.get_albuminfos(data)

        # 有些頁會取不到item
        if len(data['items']) == 0:
            logging.warning('empty url: %s' % response.url)
            return

        datadict = {item['albumId']: item for item in data['items'] if 'items' in data}
        albumdict = {album['albumId']: album for album in albums['data'] if 'data' in albums}

        # 回傳item
        for key in datadict.keys():
            if key in albumdict:
                yield self.get_item(datadict[key], albumdict[key])

    def get_albuminfos(self, data):
        """ 取得album資訊

        :param data:
        :return:
        """
        if len(data['items']) == 0:
            return

        acodes = ','.join([self.get_id(item['playUrl']) for item in data['items']])
        url = 'http://www.tudou.com/crp/getAlbumInfos.action?acodes=' + acodes
        response = requests.get(url, timeout=30)

        # set correct encoding
        fix_response_encoding(response)

        albums = json.loads(response.text)
        return albums

    def get_id(self, url):
        filename = os.path.basename(url)
        return os.path.splitext(filename)[0]

    def get_item(self, data, album):
        """ 利用data及album, 組成item

        :param data:
        :param album:
        :return:
        """
        item = MyScrapy.items.movie_content.MovieContentItem()
        item['id'] = 'td_%s' % album['albumCode']
        item['source'] = 'tudou'
        item['title'] = album['name'].strip()
        item['year'] = int(album['year'])
        # 利用lxml.html.fromstring()處理encode
        item['akas'] = [] if data['alias'].strip() == '' else [lxml.html.fromstring(data['alias'].strip()).text]
        item['imdbid'] = None
        item['content_url'] = data['playUrl']
        item['info_url'] = 'http://www.tudou.com/albumcover/%s.html' % album['albumCode']
        item['md5sum'] = hashlib.md5(json.dumps(item.__dict__, sort_keys=True)).hexdigest()
        item['udate'] = datetime.datetime.utcnow()

        return item
