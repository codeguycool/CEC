# -*- coding: utf-8 -*-

# std
import json
import logging
import re
import time

# 3rd
import requests

# proj
from lib.utils import get_useragent


class SearchDouban(object):
    """ 在豆瓣尋找符合的資料

    """

    def __init__(self, search_strategy, search_params):
        self.search_strategy = search_strategy
        self.search_params = search_params

    def search(self, kubo_item):
        retry_limit = 10
        while retry_limit > 0:
            try:
                vid = self.search_strategy.search(kubo_item, self.search_params)
                return vid
            except Exception:
                self.search_params.remove_proxy()
                retry_limit -= 1
                logging.info('retry url: %s' % self.search_strategy.url)
                time.sleep(15)
        logging.warning("max retry error, url:%s" % self.search_strategy.url)


class SearchParameters(object):

    def __init__(self, timeout=30, user_agent=None, proxy_scraper=None):
        self.timeout = timeout
        self.user_agent = user_agent if user_agent is None else get_useragent()
        self.proxy_scraper = proxy_scraper

    @property
    def proxy(self):
        if self.proxy_scraper is not None:
            return self.proxy_scraper.proxy

    def remove_proxy(self):
        if self.proxy_scraper is not None:
            self.proxy_scraper.remove(self.proxy_scraper.proxy)


class SearchStrategy(object):

    def __init__(self):
        self.url = None

    def search(self, kubo_item, search_params):
        raise NotImplementedError


class GoogleWebSearch(SearchStrategy):
    """ 利用Google搜尋頁面進行搜尋

    """

    def search(self, kubo_item, search_params):
        self.url = 'https://www.google.com.tw/search?q=%s %s %s' % (
            kubo_item['title'],
            kubo_item['year'] if kubo_item['year'] else '',
            kubo_item['stars'][0] if len(kubo_item['stars']) > 0 else ''
        )

        headers = None
        if search_params.user_agent is not None:
            headers = {'User-Agent': search_params.user_agent}
        proxies = None
        if search_params.proxy is not None:
            proxies = {search_params.proxy['schema']: search_params.proxy['url']}

        response = requests.get(self.url, headers=headers, proxies=proxies, timeout=search_params.timeout)
        if response.status_code == 200:
            pattern = '<cite>movie.douban.com/subject/(\d+)/</cite>'
            results = re.findall(pattern, response.text)
            if len(results) > 0:
                return results[0]
        else:
            logging.warning(
                'url: %s, http status: %d, proxy: %s' % (self.url, response.status_code, search_params.proxy['url'])
            )


class DoubanApiStragety(SearchStrategy):
    """ 利用 Douban Search API 進行搜尋

    """
    def search(self, kubo_item, search_params):
        self.url = 'https://api.douban.com/v2/movie/search?q=%s %s %s' % (
            kubo_item['title'],
            kubo_item['year'] if kubo_item['year'] else '',
            kubo_item['stars'][0] if len(kubo_item['stars']) > 0 else ''
        )

        headers = None
        if search_params.user_agent is not None:
            headers = {'User-Agent': search_params.user_agent}
        proxies = None
        if search_params.proxy is not None:
            proxies = {search_params.proxy['schema']: search_params.proxy['url']}

        response = requests.get(self.url, headers=headers, proxies=proxies, timeout=search_params.timeout)
        if response.status_code == 200:
            result = json.loads(response.content)
            return self._get_vid(result, kubo_item)
        else:
            logging.warning(
                'url: %s, http status: %d, proxy: %s' % (self.url, response.status_code, search_params.proxy['url'])
            )

    def _get_vid(self, result, kubo_item):
        for subject in result['subjects']:
            if subject['subtype'] != 'tv':
                break
            if subject['year'] != str(kubo_item['year']):
                break
            if subject['alt'].find('movie.douban.com/subject') == -1:
                break

            pattern = 'movie.douban.com/subject/(\d+)/'
            results = re.findall(pattern, subject['alt'])
            if len(results) > 0:
                return results[0]