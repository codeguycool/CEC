# -*- coding: utf-8 -*-

# proj
from lib.utils import get_useragent


class RotateUserAgentMiddleware(object):

    def __init__(self, user_agent=''):
        self.user_agent = user_agent

    def process_request(self, request, spider):
        ua = get_useragent()
        if ua:
            request.headers.setdefault('User-Agent', ua)
