# -*- coding: utf-8 -*-

# std
import datetime
import hashlib
import json
import logging
import sys
import unicodedata

# 3rd
import lxml.html
import requests
import scrapy
import youtube_dl

# project
from lib.utils import fix_response_encoding

# 標點符號表
tbl = dict.fromkeys(i for i in xrange(sys.maxunicode) if unicodedata.category(unichr(i)).startswith('P'))
tbl[ord('~')] = None  # '~' 沒有分類在'P'裡，因為該符號被分類為數學運算
tbl = {key: u' ' for key in tbl}


def remove_punctuation(text):
    """ 移除字串的標點符號

    透過unicode的category開點為P的規則建立標點符號表，再將符合標點符號表的字做轉換。

    :param text:
    :return:
    """
    return text.translate(tbl)


def get_keywords(text):
    """ 取得處理過的keywords

    將字串轉小寫，去除標點符號，利用空白去切token，再將token排序

    :param text:
    :return:
    """
    keywords = text.lower()
    keywords = keywords.translate(tbl)
    keywords = keywords.split(' ')
    keywords = filter(None, keywords)
    keywords.sort()
    keywords = ' '.join(keywords)
    return keywords


class KtvItem(scrapy.Item):

    source = scrapy.Field()
    type = scrapy.Field()
    lang = scrapy.Field()
    title = scrapy.Field()
    artist = scrapy.Field()
    keywords = scrapy.Field()
    keymd5 = scrapy.Field()
    rank = scrapy.Field()
    udate = scrapy.Field()
    youtube = scrapy.Field()

    def __init__(self, source, song_type, lang, title, artist, rank):
        scrapy.Item.__init__(self)
        self['source'] = source
        self['lang'] = lang
        self['title'] = title
        self['artist'] = artist

        if song_type is not None:
            self['type'] = song_type
        if rank is not None:
            self['rank'] = rank

        # youtube 的 search term
        search_term = '%s %s' % (title, artist)
        # 取得轉化過的唯一值做為 keywords, 用來做為 md5 之用
        keywords = get_keywords(search_term)

        self['keywords'] = keywords
        self['keymd5'] = hashlib.md5(keywords.encode('utf-8')).hexdigest()
        self['udate'] = datetime.datetime.utcnow()
        self['youtube'] = YoutubeKtvQuery().get_match_video(search_term)

        # content(youtube)的資訊, 在pipeline中會用到, 用來存進song_content
        if self['youtube']:
            self['youtube']['keymd5'] = self['keymd5']
            self['youtube']['udate'] = datetime.datetime.utcnow()

    def islist(self):
        return True if 'type' in self and 'lang' in self else False


class YoutubeKtvQuery(object):
    """

    在 Youtube 找尋符合的 Ktv 資料

    """

    def get_match_video(self, search_term):
        """ 找到符合的 KTV video

        :param search_term: search term
        :return: youtube_dl info
        """
        if search_term is None:
            raise Exception("search_term can't be None")
        vid = self.get_match_vid(search_term)
        if vid:
            return self.parse_youtube_info(vid)

    def parse_youtube_info(self, vid):
        """ 將youtube_dl的info轉成我們要的資訊格式

        :param vid:
        :return:
        """
        if vid is None:
            raise Exception("vid can't be None")

        videourl = 'http://www.youtube.com/watch?v=' + vid
        ydl = youtube_dl.YoutubeDL()

        try:
            video_info = ydl.extract_info(videourl, download=False)
            if video_info:
                content = dict()
                content['source'] = 'youtube'
                content['uploader'] = video_info['uploader'] if 'uploader' in video_info else None
                content['upload_date'] = video_info['upload_date']
                content['duration'] = video_info['duration'] if 'duration' in video_info else None
                content['poster_url'] = video_info['thumbnail'] if 'thumbnail' in video_info else None
                content['play_url'] = video_info['webpage_url']
                content['fullname'] = video_info['title']
                content['description'] = video_info['description'] if 'description' in video_info else None
                content['description'] = video_info['description'] if video_info['description'] != '' else None
                content['content'] = json.dumps(self.extract_format(video_info), ensure_ascii=False, sort_keys=True)
                content['md5sum'] = hashlib.md5(json.dumps(content)).hexdigest(),
                return content
        except youtube_dl.DownloadError as e:
            logging.error(e.message)

    def extract_format(self, video_info):
        formats = video_info['formats']
        resolution = []
        acodec = None
        for fmt in formats:
            # 找出純影像檔做為解析度
            if fmt.get('vcodec', 'none') != 'none' and fmt.get('acodec', 'none') == 'none' and fmt['ext'] != 'webm':
                resolution.append((fmt['height'], fmt['format_id']))
            # 找出純音效檔做為音效來源
            if fmt.get('acodec', 'none') != 'none':
                # 找出最好的格式
                if int(fmt['format_id']) > acodec:
                    acodec = fmt['format_id']

        if resolution:
            # {'360': 18 + 235}
            format_dict = {res[0]: '%s+%s' % (res[1], acodec) for res in resolution}
        else:
            # 如果沒找到純影像檔，那就取得目前的格式
            format_dict = {str(video_info['height']): video_info['format_id']}
        return format_dict

    def get_videos(self, term):
        """ 取回利用search_term在youtube搜尋的第一頁結果

        :param term:
        :return:
        """
        # 失戀無罪 A-Lin => 失戀無罪 A-Lin ktv
        query_term = '%s ktv' % term
        # 失戀無罪+A-Lin+ktv
        query_term = query_term.replace(' ', '+')
        queryurl = "https://www.youtube.com/results?lclk=video&filters=video&search_query=" + query_term
        response = requests.get(queryurl, timeout=30)

        # set correct encoding
        fix_response_encoding(response)

        if response.ok:
            body = lxml.html.fromstring(response.text)
            videos = body.xpath("//div[contains(@class, 'yt-lockup-video')]")
            return videos

    def get_match_vid(self, term):
        """ 找出符合規則的vid(video id)

        YouTube 搜尋 "歌曲+人名+KTV"，排除廣告從頭開始取十部影片名稱字串
        rules:
        1. 若有同時包含"歌曲、人名、KTV"即為目標
        2. 除了1的狀況外，同時包含"歌曲、人名、Official/官方"即為目標
        3. 除了1.2的狀況外，同時包含"歌曲、人名、MV"即為目標
        4. 其他狀況則放棄將此歌曲列進歌單

        :param term:
        :return: vid or none
        """
        videos = self.get_videos(term)

        # 最多只檢查前面10筆資料
        max_length = 0

        if videos:
            max_length = 10 if len(videos) >= 10 else len(videos)

        for i in xrange(0, max_length):
            video = videos[i]
            title = unicode(video.xpath("./div/div[@class='yt-lockup-content']/h3/a/text()")[0])
            vid = unicode(video.xpath('./@data-context-item-id')[0])
            if self.is_keyword_in(title, '%s ktv' % term):
                return vid
            if self.is_keyword_in(title, '%s Official' % term):
                return vid
            if self.is_keyword_in(title, u'%s 官方' % term):
                return vid
            if self.is_keyword_in(title, '%s MV' % term):
                return vid

    def is_keyword_in(self, title, keywords):
        """ 標題是否符合keywords

        :param title:
        :param keywords:
        :return:
        """
        # 失戀無罪 A-Lin => [失戀無罪,a,lin]
        keyword_list = remove_punctuation(keywords.lower()).split(' ')
        keyword_list = filter(None, keyword_list)
        # [失戀無罪,a,lin] => [a,lin,失戀無罪]
        keyword_list.sort()

        for keyword in keyword_list:
            if title.lower().find(keyword) == -1:
                return False
        return True
