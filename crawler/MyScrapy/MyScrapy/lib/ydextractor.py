# -*- coding: utf-8 -*-

# std
import time

# 3rd
import requests
from scrapy.selector import Selector

# proj
from lib.utils import parse_urlparams, fix_response_encoding
from MyScrapy.lib import IVideoResourceExtractor, VideoResource


class YDExtractor(IVideoResourceExtractor):
    """ 擷取酷播的Youtube、Dailymtoion影片

    """

    def get_video_resources(self, links):
        video_resource = VideoResource()
        eps_resources = self.get_eps_resources(links)
        for source in ['youtube', 'dailymotion']:
            # add new resource
            video_resource.add_resource(source)
            # fit eps in resource
            for resource in eps_resources:
                video_resource.add_ep(source, resource.data['title'], resource.data['url'], resource.data[source])
            # del empty resource
            if video_resource.is_empty_resource(source):
                video_resource.del_resource(source)
        return video_resource

    def get_eps_resources(self, eplinks):
        """ 取出每一集的 resource

        :param eplinks:
        :return:
        """
        eps_resources = []
        for eplink in eplinks:
            eps_resources.append(KuboYoutubeResource(eplink))
        return eps_resources


class KuboYoutubeResource(object):

    def __init__(self, url):
        response = requests.get(url, headers={'referer': url}, timeout=30)

        # set correct encoding
        fix_response_encoding(response)

        if response.status_code == 200:
            self.selector = Selector(text=response.text)
        time.sleep(2)
        self.data = {
            'title': self.get_title(),
            'url': url,
            'youtube': self.get_youtue_urls(),
            'dailymotion': self.get_dailymotion_urls()
        }

    def get_title(self):
        return self.selector.xpath('//title/text()').extract()[0]

    def get_youtue_urls(self):
        vids = self.selector.re("id:'([^']*)'")
        return ['http://www.youtube.com/watch?v=%s' % vid for vid in vids]

    def get_dailymotion_urls(self):
        """ 取出 dailymotion 的 url

        :return:
        """
        dailymotion_urls = []
        xpath = "//iframe[contains(@src, 'www.123kubo.com/168player/dmplayer.php?url=')]/@src"
        if self.selector.xpath(xpath):
            playerurl = self.selector.xpath(xpath).extract()[0]
            vids = self.get_dailymotion_vids(playerurl)
            dailymotion_urls = ['http://www.dailymotion.com/video/%s' % vid for vid in vids]
        return dailymotion_urls

    def get_dailymotion_vids(self, playerurl):
        """ 取出 dailymotion 的vid

        :param playerurl: http://www.123kubo.com/168player/dmplayer.php?url=k3U5AJgepu9Uw1cxybd,k1CRVRlaQwQDbFcxynD
        :return: vid list
        """
        params = parse_urlparams(playerurl)
        if 'url' in params:
            # params['url'] = ['k3U5AJqep9w,k1565lxsdfq'], two part in one param
            return filter(None, ','.join(params['url']).split(','))
        return []
