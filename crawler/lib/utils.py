# -*- coding: utf-8 -*-

# std
import random
import urlparse

# 3rd
import requests


def get_useragent():
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]

    return random.choice(user_agent_list)


def parse_urlparams(url):
    """ 解析出 url 的參數

    :param url: http://www.123kubo.com/168player/dmplayer.php?url=k3U5AJgepu9Uw1cxybd,k1CRVRlaQwQDbFcxynD&autoplay=0
    :return: {'url': ['k3U5AJgepu9Uw1cxybd,k1CRVRlaQwQDbFcxynD'], 'autoplay': ['0']}
    """
    result = urlparse.urlparse(url)
    tokens = urlparse.parse_qs(result.query)
    return tokens


def fix_response_encoding(response):
    """ set correct response encoding

    1. get encoding from content
    2. if encoding not in content, get encoding from header(response.encoding)
    3. if encoding not in header, get encoding from chardet(response.apparent_encoding)

    :param response:
    :return:
    """

    def _encoding_in_header_is_invalidate(_response):
        return not _response.encoding or _response.encoding == 'ISO-8859-1'

    if response.status_code != 200:
        return

    # get encoding from content
    content_encoding = requests.utils.get_encodings_from_content(response.content)
    if content_encoding and response.encoding != content_encoding[0]:
        response.encoding = content_encoding[0]
        return

    # get encoding from response.apparent_encoding
    if _encoding_in_header_is_invalidate(response):
        response.encoding = response.apparent_encoding
        return
