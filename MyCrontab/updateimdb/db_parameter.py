# -*- coding: utf-8 -*-


class DbHost(object):

    def __init__(self, hostname, port=5432):
        self.HostName = hostname
        self.port = port


class DbUser(object):

    def __init__(self, username, password=None):
        self.UserName = username
        self.Password = password
