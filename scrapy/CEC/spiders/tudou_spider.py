# -*- coding: utf-8 -*-

""" 土豆的網路爬蟲

"""

# std lib
import hashlib
import json
import os
import sys
import urlparse

# 3rd lib
import lxml.html
import scrapy
import requests

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj lib
import CEC.settings
import CEC.items.content_item


class TudouSpider(scrapy.Spider):
    """ Get Tudou All free movie content(http://www.tudou.com/list/ach5a-2b-2c-2d-2e1309f998g-2h-2i-2j-2k-2l-2m-2n-2sort2.html)

    """
    name = 'tudou'
    allowed_domains = ['tudou.com']
    start_urls = ['http://www.tudou.com/s3portal/service/pianku/data.action?pageSize=90&app=mainsitepc&deviceType=1&tags=998&tagType=3&firstTagId=5&areaCode=710000&initials=&hotSingerId=&pageNo=1&sortDesc=quality']
    custom_settings = {
        'ITEM_PIPELINES': {'CEC.pipelines.content_pipeline.ContentPipeline': 300}
    }

    def getid(self, url):
        filename = os.path.basename(url)
        return os.path.splitext(filename)[0]

    def getalbuminfos(self, data):
        """ 取得album資訊

        :param data:
        :return:
        """
        url = 'http://www.tudou.com/crp/getAlbumInfos.action?acodes=' + ','.join([self.getid(item['playUrl']) for item in data['items']])
        response = requests.get(url)
        albums = json.loads(response.text)
        return albums

    def get_item(self, data, album):
        """ 利用data及album, 組成item

        :param data:
        :param album:
        :return:
        """
        item = CEC.items.content_item.ContentItem()

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

        return item

    def parse(self, response):
        # 取得data資訊
        data = json.loads(response.body)
        if len(data['items']) == 0:
            print response.url
            return
        # 取得album資訊
        albums = self.getalbuminfos(data)

        datadict = {item['albumId']: item for item in data['items']}
        albumdict = {album['albumId']: album for album in albums['data']}

        # 回傳item
        for key in datadict.keys():
            if key in albumdict:
                yield self.get_item(datadict[key], albumdict[key])

        qs = urlparse.urlparse(response.url)
        tokens = urlparse.parse_qs(qs.query)

        # 處理分頁
        if tokens['pageNo'][0] == '1':
            total = int(data['total'])
            pagecount = total / 90
            for i in xrange(2, pagecount + 1):
                yield scrapy.Request('http://www.tudou.com/s3portal/service/pianku/data.action?pageSize=90&app=mainsitepc&deviceType=1&tags=998&tagType=3&firstTagId=5&areaCode=710000&initials=&hotSingerId=&pageNo=%d&sortDesc=quality' % i, callback=self.parse)

if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(TudouSpider)
    process.start()