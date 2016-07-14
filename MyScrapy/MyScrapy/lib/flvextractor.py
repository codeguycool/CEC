# -*- coding: utf-8 -*-

# std
import logging
import urlparse

# 3rd
import requests

# proj
from MyScrapy.lib import IVideoResourceExtractor, VideoResource
from MyScrapy.lib.jsexecute import Js2PyExecutor


class FlvExtractor(IVideoResourceExtractor):
    """ 擷取酷播的FLV影片，FLV包括有Youku、Tudou、GoogleDrive...等來源

    """

    def __init__(self, jsexecutor=None):
        self.jsexecutor = jsexecutor
        if jsexecutor is None:
            self.jsexecutor = Js2PyExecutor()

    def get_video_resources(self, links):
        """ 取出不同來源裡的影片

        FlvExtractor 是利用 javascript 取出影片列表，再轉成 video resources 格式

        :param links:
        :return:
        """

        video_resources = VideoResource()

        if len(links) == 0:
            return video_resources

        url = links[0]
        for data in self.get_playdata(url):
            playdata = PlayData(url, data)
            video_resources.update(playdata.get_resource())

        return video_resources

    def get_playdata(self, url):
        """ 取得酷播的藏在javascript裡的影片列表

        :param url:
        :return:
        [{
            "servername": null,
            "playname": "xigua",
            "playurls": [
                [
                    "殭国语01.mkv",
                    "ftp://a.gbl.114s.com:20320/4422/殭国语01.mkv",
                    "/vod-play-id-82698-sid-0-pid-1.html"
                ],
                [
                    "殭国语02.mkv",
                    "ftp://a.gbl.114s.com:20320/1525/殭国语02.mkv",
                    "/vod-play-id-82698-sid-0-pid-2.html"
                ]
            ]
        }, {
            "servername": null,
            "playname": "bj58",
            "playurls": [
                [
                    "殭國語01",
                    "fun58_756xPfUP%2FBnVcLgrsGABxA9JAVH7vs1Is2QVrFm2Xqo%3D",
                    "/vod-play-id-82698-sid-2-pid-1.html"
                ],
                [
                    "殭國語02(影像有問題介意者勿點)",
                    "fun58_k%2BC2MosJD0Zd1HxdnGkfy7PIhyuq2m9YY2OJWloA0BA%3D",
                    "/vod-play-id-82698-sid-2-pid-2.html"
                ]
            ]
        }]
        """
        playdata = []
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            logging.warning('url: %s, http status: %d' % (url, response.status_code))
        else:
            playdata = self.jsexecutor.get_playdata(response.text)['Data']
        return playdata


class PlayData(object):
    """ 將酷播的PlayData以class呈現

    """

    def __init__(self, url, data):
        """

        :param url: http://www.123kubo.com/vod-play-id-82698-sid-2-pid-1.html
        :param data:
        {
            "servername": null,
            "playname": "bj58",
            "playurls": [
                [
                    "殭國語01",
                    "fun58_756xPfUP%2FBnVcLgrsGABxA9JAVH7vs1Is2QVrFm2Xqo%3D",
                    "/vod-play-id-82698-sid-2-pid-1.html"
                ],
                [
                    "殭國語02(影像有問題介意者勿點)",
                    "fun58_k%2BC2MosJD0Zd1HxdnGkfy7PIhyuq2m9YY2OJWloA0BA%3D",
                    "/vod-play-id-82698-sid-2-pid-2.html"
                ]
            ]
        }
        :return:
        """
        self.url = url
        self.name = data['playname']
        self.eps = data['playurls']

    def get_resource(self):
        resource = VideoResource()
        # fixme: 如果有要增加新的來源
        extractor = {
            'bj': YoukuExtractor(),
            'bj5': LetvExtractor(),
            'bj7': SohoExtractor(),
            'bj10': IqiyiExtractor(),
            'bj11': TudouExtractor(),
            'bj58': GoogleDriveExtractor()
        }.get(self.name)
        if extractor:
            resource.add_resource(extractor.name)
            for ep in self.eps:
                title = ep[0]
                play_url = urlparse.urljoin(self.url, ep[2])
                video_urls = [extractor.geturl(ep[1])] if extractor.geturl(ep[1]) is not None else []
                resource.add_ep(extractor.name, title, play_url, video_urls)
        return resource


class UrlExtractor(object):

    @property
    def name(self):
        return self.getname()

    def getname(self):
        raise NotImplementedError

    def geturl(self, playid):
        raise NotImplementedError


class YoukuExtractor(UrlExtractor):

    def getname(self):
        return 'youku'

    def geturl(self, playid):
        """ 取得優酷的播放網址

        XNDM3NTI5OTMy_wd1 => http://v.youku.com/v_show/id_XNDM3NTI5OTMy.html

        :param playid: 酷播的優酷id
        :return:
        """

        position = playid.find('_wd1')
        if position > 0:
            return 'http://v.youku.com/v_show/id_%s.html' % playid[:position]


class LetvExtractor(UrlExtractor):

    def getname(self):
        return 'letv'

    def geturl(self, playid):
        """ 取得樂視的播放網址

        fun1_1740428.html => http://www.letv.com/ptv/vplay/1740428.html

        :param playid: 酷播的樂視id
        :return:
        """

        if playid.find('fun1_') == 0:
            return 'http://www.letv.com/ptv/vplay/%s' % playid[5:]


class SohoExtractor(UrlExtractor):

    def getname(self):
        return 'sohu'

    def geturl(self, playid):
        """ 取得搜狐的播放網址

        fun5_20130415/n372763492.shtml => http://tv.sohu.com/20130415/n372763492.shtml

        :param playid: 酷播的搜狐id
        :return:
        """

        if playid.find('fun5_') == 0:
            return 'http://tv.sohu.com/%s' % playid[5:]


class IqiyiExtractor(UrlExtractor):

    def getname(self):
        return 'iqiyi'

    def geturl(self, playid):
        """ 取得愛奇藝的播放網址

        fun8_19rrok4nt0.html => http://www.iqiyi.com/v_19rrok4nt0.html

        :param playid:
        :return:
        """

        if playid.find('fun8_') == 0:
            return 'http://www.iqiyi.com/v_%s' % playid[5:]


class TudouExtractor(UrlExtractor):

    def getname(self):
        return 'tudou'

    def geturl(self, playid):
        """ 取得土豆的播放網址

        fun10_QicvhYGdl24/mtJbynl97xE.html => http://www.tudou.com/albumplay/QicvhYGdl24/mtJbynl97xE.html

        :param playid: 酷播的土豆id
        :return:
        """

        if playid.find('fun10_') == 0:
            return 'http://www.tudou.com/albumplay/%s' % playid[6:]


class GoogleDriveExtractor(UrlExtractor):

    def getname(self):
        return 'googledrive'

    def geturl(self, playid):
        if playid.find('fun58_') == 0:
            return 'http://www.123kubo.com/168player/?url=fun58_%s' % playid[6:]
