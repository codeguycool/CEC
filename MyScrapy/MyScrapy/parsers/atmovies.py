# -*- coding: utf-8 -*-

# std
import logging
import re
import urlparse

# std
from scrapy.selector import Selector

# project
from MyScrapy.items.movie import MovieItem
from MyScrapy.lib.extractor import XpathExtractor, ValueExtract
from MyScrapy.lib.htmlcache import HtmlCache
from MyScrapy.lib.pathstrategy import SubdirNameByPrefixFilepath, SubdirNameBySuffixFilepath
from MyScrapy.parsers import WebParser


class AtmoviesParser(WebParser):

    def _get_htmlcache(self):
        return HtmlCache(
            self.url, self._get_urlid(),
            old_filepath_inst=SubdirNameBySuffixFilepath(suffix_num=3),
            filepath_inst=SubdirNameByPrefixFilepath(prefix_num=2)
        )

    def _get_urlid(self):

        if 'ww2' in self.url:
            parsed_url = urlparse.urlparse(self.url)
            params = urlparse.parse_qs(parsed_url.query)
            if params['filmid']:
                return params['filmid'][0].lower()
        else:
            result = re.search('app2.atmovies.com.tw/film(.*)/', self.url)
            if result:
                return result.groups(0)[0].lower()
            else:
                raise Exception("can't find filmid parameter")

    def _get_extractors(self):
        return [
            XpathExtractor(
                'title', self.html,
                "//span[@class='ratingbutton']/a/@href",
                postback=self.get_title
            ),
            XpathExtractor(
                'akas', self.html,
                "//div[@class='filmTitle']/text()",
                postback=self.get_akas
            ),
            XpathExtractor(
                'runtimes', self.html,
                "string(//ul[@class='runtime'])",
                postback=self.get_runtimes
            ),
            XpathExtractor(
                'releaseDate', self.html,
                "string(//ul[@class='runtime'])",
                postback=self.get_releaseDate
            ),
            ValueExtract(
                'directors', self.get_directors
            ),
            ValueExtract(
                'writers', self.get_writers
            ),
            ValueExtract(
                'stars', self.get_stars
            ),
            XpathExtractor(
                'year', self.html,
                u"//div[@id='filmCastDataBlock']/ul/li/b[text()='影片年份：']/following-sibling::text()[1]",
                postback=self.get_year
            ),
            XpathExtractor(
                'thumbnailurl', self.html,
                "//div[@id='filmTagBlock']/span[1]/a[@class='image Poster']/img/@src",
                postback=self.remove_default_image
            ),
            ValueExtract(
                'posterurl', None, postback=self.get_posterurl
            ),
            XpathExtractor(
                'countries', self.html,
                u"//div[@id='filmCastDataBlock']/ul/li/b[text()='出  品  國：']/following-sibling::text()[1]",
                postback=self.split_countries
            ),
            XpathExtractor(
                'languages', self.html,
                u"//div[@id='filmCastDataBlock']/ul/li/b[text()='語　　言：']/following-sibling::text()[1]",
                postback=self.split_languages
            ),
            XpathExtractor(
                'imdbid', self.html,
                "//div[@id='filmCastDataBlock']/ul/li/a[text()='IMDb']/@href",
                postback=self.get_imdbid
            ),
            XpathExtractor(
                'description', self.html,
                "normalize-space(string(//comment()[contains(.,'Story info start')]/..))",
                postback=self.get_description
            ),

            ValueExtract('source', 'atmovies'),
            ValueExtract('id', self.get_id()),
            ValueExtract('kind', 'movie'),
            ValueExtract('genres', []),
            ValueExtract('rating', None),
            ValueExtract('url', self.url),
        ]

    def _get_item(self):
        return MovieItem()

    def parse(self):
        if self.extractors is not None and self.item is not None:
            for extractor in self.extractors:
                self.item[extractor.label] = extractor.extract()

            # 若title為空，則代表是空白網頁，不繼續處理
            if self.item['title'] is None:
                self.item = None
                return

    def get_title(self, rating_url):
        # 可能空白網頁,例: http://ww2.atmovies.com.tw/film/film.cfm?filmid=fdatm0894138
        if rating_url is None:
            logging.info('empty page, url: %s' % self.url)
            return
        qs = urlparse.urlparse(rating_url)
        params = urlparse.parse_qs(qs.query.encode('utf-8'))
        if 'filmtitle' in params:
            return params['filmtitle'][0].decode('utf-8')

    def get_akas(self, title):
        if self.item['title'] is not None:
            return [title.replace(self.item['title'], '').strip()]
        else:
            self.item['title'] = title
            return [title]

    def get_tokens(self, rawtext):
        """

        :param rawtext:  片長：106分 上映日期：2016/02/09 廳數 (79) 台北票房：13,472萬
        :return:
        """
        tokens = rawtext.split()
        tokens = [token.strip() for token in tokens]  # ["片長：106分", "上映日期：2016/02/09"]
        token_dict = {}
        for token in tokens:
            if token.find(u'：') > 1:
                k, v = token.split(u'：')
                token_dict[k] = v  # {"片長": "106分", "上映日期": "2016/02/09"}
        return token_dict

    def get_runtimes(self, rawtext):
        tokens = self.get_tokens(rawtext)
        runtime = tokens.get(u'片長')
        if runtime is not None:
            return runtime.replace(u'分', '')

    def get_releaseDate(self, rawtext):
        tokens = self.get_tokens(rawtext)
        releasedate = tokens.get(u'上映日期')
        if releasedate is not None:
            return {'Default': releasedate, 'TW': releasedate}
        else:
            return {}

    def get_year(self, year):
        return year if year != '' else None

    def remove_default_image(self, thumbnailurl):
        if thumbnailurl == "http://images.atmovies.com.tw/images/spacer.gif":
            return None
        else:
            return thumbnailurl

    def get_posterurl(self, posterurl):
        if self.item['year'] is not None and self.item['thumbnailurl'] is not None:
            tokens = self.item['thumbnailurl'].split('/')
            if len(tokens) != 9:
                logging.info(self.item['thumbnailurl'])
                return
            prefix = tokens[5]
            vid = tokens[6]
            filename = tokens[8]
            posterurl = 'http://l10l010l3322l1.photos.atmovies.com.tw:8080/film/%s/%s/%s/poster/%s' \
                          % (str(self.item['year']), prefix, vid, filename.replace('pl_', 'px_'))
            return posterurl

    def get_cast_dict(self):
        """ 取得導演、編劇、演員等資訊

        :return:
        """
        key = None
        info = {}
        key_dict = {
            u'導演：': 'directors',
            u'編劇：': 'writers',
            u'演員：': 'stars'
        }
        for li in self.selector.xpath("//div[@id='filmCastDataBlock']/ul[1]/li[position() < last()]"):
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

    def get_directors(self, directors):
        cast = self.get_cast_dict()
        if cast:
            return cast.get('directors', [])

    def get_writers(self, get_writers):
        cast = self.get_cast_dict()
        if cast:
            return cast.get('writers', [])

    def get_stars(self, stars):
        cast = self.get_cast_dict()
        if cast:
            return cast.get('stars', [])

    def split_item(self, item):
        item = item.replace(u'、', ',')
        item = item.replace(u'／', ',')
        item = item.replace('/', ',')
        item = item.replace('|', ',')
        item = item.replace('&', ',')
        return filter(None, item.strip().split(','))

    def split_countries(self, countries):
        if countries is not None:
            return self.split_item(countries)

    def split_languages(self, languages):
        if languages is not None:
            return self.split_item(languages)

    def get_description(self, description):
        description = description.replace(u'劇情簡介', '') if description is not None else description
        description = description.replace(u'本片尚無介紹資料 ◎＿◎', '') if description is not None else description
        return description

    def get_imdbid(self, imdbid):
        if imdbid is not None:
            return imdbid.replace('http://us.imdb.com/Title?', 'tt')

    def get_id(self):
        return 'am_%s' % self._get_urlid()
