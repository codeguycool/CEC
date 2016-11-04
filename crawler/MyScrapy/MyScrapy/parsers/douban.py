# -*- coding: utf-8 -*-

# std
import logging
import os
import re

# project
from MyScrapy.items.movie import MovieItem
from MyScrapy.items.tv import TvItem
from MyScrapy.lib.extractor import XpathExtractor, ValueExtract
from MyScrapy.lib.htmlcache import HtmlCache
from MyScrapy.lib.pathstrategy import SubdirNameBySuffixFilepath, SubdirNameByPrefixFilepath
from MyScrapy.parsers import WebParser


def split_item(item):
    if not isinstance(item, list) and item is not None:
        return item.split('/')
    elif isinstance(item, list):
        return item
    else:
        return []


class BaseDoubanParser(WebParser):
    """
    共同欄位的豆瓣 Parser

    """

    def _get_htmlcache(self):
        return HtmlCache(
            self.url, self._get_urlid(),
            old_filepath_inst=SubdirNameBySuffixFilepath(suffix_num=3),
            filepath_inst=SubdirNameByPrefixFilepath(prefix_num=3)
        )

    def _get_urlid(self):
        pattern = '//movie\.douban\.com/subject/(\d+)'
        result = re.search(pattern, self.url)
        if result and result.group(1) != '':
            return result.group(1)
        else:
            raise Exception("can't find id")

    def _get_extractors(self):
        common_extractors = [
            XpathExtractor(
                'title', self.html,
                "//title/text()",
                postback=self.get_title_name
            ),
            XpathExtractor(
                'subtitle', self.html,
                "//div[@id='content']/h1/span[@property='v:itemreviewed']/text()",
                postback=self.get_subtitle
            ),
            XpathExtractor(
                'akas', self.html,
                u"//div[@id='info']/span[text()='又名:']/following-sibling::text()",
                postback=self.get_akas
            ),
            XpathExtractor(
                'posterurl', self.html,
                "//div[@id='mainpic']//img[@rel='v:image']/@src",
                postback=self.get_posterurl
            ),
            XpathExtractor(
                'genres', self.html,
                "//div[@id='info']/span[@property='v:genre']/text()",
                islist=True
            ),
            XpathExtractor(
                'year', self.html,
                "//div[@id='content']/h1/span[@class='year']/text()",
                postback=self.get_year_number
            ),
            XpathExtractor(
                'stars', self.html,
                "//a[@rel='v:starring']/text()",
                islist=True, postback=split_item
            ),
            XpathExtractor(
                'imdbid', self.html,
                u"//div[@id='info']/span[text()='IMDb链接:']/following-sibling::a/text()"
            ),
            XpathExtractor(
                'description', self.html,
                "normalize-space(string(//span[@property='v:summary']))"
            ),
            ValueExtract('source', 'douban'),
            ValueExtract('id', self.get_dbid()),
            ValueExtract('url', self.url),
        ]
        total_extractors = common_extractors
        total_extractors.extend(self._get_concreate_extractors())
        return total_extractors

    def _get_concreate_extractors(self):
        raise NotImplementedError

    def _get_item(self):
        raise NotImplementedError

    def get_title_name(self, title):
        index = title.rfind(u'(豆瓣)')
        return title[:index + -1].strip()

    def get_subtitle(self, titles):
        subtitle = titles[len(self.item['title']):].strip()
        return subtitle if subtitle != '' else None

    def get_akas(self, akas):
        akas = akas if akas else ''
        akas = akas.split('/')
        if self.item['subtitle'] is not None:
            akas.append(self.item['subtitle'])
        return akas

    def get_dbid(self):
        return 'db_' + self._get_urlid()

    def get_posterurl(self, posterurl):
        if posterurl.find('/mpic/') > -1:
            posterurl = posterurl.replace('/mpic/', '/lpic/')
        elif posterurl.find('/view/movie_poster_cover/spst/public/') > -1:
            posterurl = posterurl.replace('/movie_poster_cover/spst/public/', '/photo/photo/public/')

        # 檢查是不是gif檔，gif是預設的圖片類型
        filename, ext = os.path.splitext(posterurl)
        if ext.lower() != '.gif':
            return posterurl

    def get_year_number(self, year):
        return year[1:5] if year is not None else None


class DoubanMovieParser(BaseDoubanParser):
    """ 豆瓣的電影 Parser

    """

    def _get_concreate_extractors(self):
        return [
            XpathExtractor(
                'thumbnailurl', self.html,
                "//div[@id='mainpic']//img[@rel='v:image']/@src",
                postback=self.get_thumbnailurl
            ),
            XpathExtractor(
                'directors', self.html,
                "//a[@rel='v:directedBy']/text()", islist=True, postback=split_item
            ),
            XpathExtractor(
                'writers', self.html,
                u"//div[@id='info']/span/span[text()='编剧']/following-sibling::span/a/text()",
                islist=True, postback=split_item
            ),
            XpathExtractor(
                'countries', self.html,
                u"//div[@id='info']/span[text()='制片国家/地区:']/following-sibling::text()[1]",
                postback=split_item
            ),
            XpathExtractor(
                'languages', self.html,
                u"//div[@id='info']/span[text()='语言:']/following-sibling::text()[1]",
                postback=split_item
            ),
            XpathExtractor(
                'releaseDate', self.html,
                "//div[@id='info']/span[@property='v:initialReleaseDate']/@content",
                islist=True, postback=self.normalize_releasedate
            ),
            XpathExtractor(
                'runtimes', self.html,
                "//div[@id='info']/span[@property='v:runtime']/@content"
            ),
            ValueExtract('kind', None, postback=self.get_kind),
            ValueExtract('rating', None),
        ]

    def _get_item(self):
        return MovieItem()

    def get_thumbnailurl(self, thumbnailurl):
        return self.item['posterurl']

    def normalize_releasedate(self, releasedates):
        releasedate_dict = {}
        for releasedate in releasedates:
            result = re.search('([^\(]*)(\(.*\))?', releasedate)
            if result:
                # 1944-12-21(墨西哥) (premiere)、1944-12-21(墨西哥)
                key = result.group(2) if result.group(2) is not None else 'Default'
                value = result.group(1).strip()
                releasedate_dict[key] = value
        if len(releasedate_dict) > 0 and ('Default' not in releasedate_dict):
            releasedate_dict['Default'] = releasedate_dict.values()[0]
        return releasedate_dict

    def get_kind(self, kind):
        kind_xpath = "//a[contains(@data-url, '//movie.douban.com/subject/%s/')]/@data-type" % self.item['id'][3:]
        if len(self.selector.xpath(kind_xpath)) == 0:
            logging.debug(self.item['url'])
        kind = self.selector.xpath(kind_xpath)[0].extract()
        kind = {u"电影": 'movie'}.get(kind)
        if kind != 'movie':
            logging.info('%s is not movie' % self.item['url'])
        return kind


class DoubanTvParser(BaseDoubanParser):
    """ 豆瓣的電視劇 Parser

    """

    def __init__(self, url, kind):
        self.kind = kind
        BaseDoubanParser.__init__(self, url)

        if not self.is_tv():
            logging.info("%s is not tv type" % url)
            self.item = None

    def _get_item(self):
        return TvItem()

    def _get_concreate_extractors(self):
        return [
            XpathExtractor(
                'region', self.html,
                u"//div[@id='info']/span[text()='制片国家/地区:']/following-sibling::text()[1]"
            ),
            ValueExtract('dbid', self._get_urlid()),
            ValueExtract('kind', self.kind),
        ]

    def is_tv(self):
        data_type_element = self.selector.xpath("//a[contains(@data-url, 'movie.douban.com/subject')]/@data-type")
        if len(data_type_element) == 0:
            return False
        if data_type_element[0].extract().strip() != u'电视剧':
            return False
        return True
