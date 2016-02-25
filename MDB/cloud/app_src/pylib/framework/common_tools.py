# -*-coding: utf-8 -*-
"""Common function
"""
import collections


def unicode2str(data):
    if isinstance(data, basestring):
        if isinstance(data, str):
            return data
        return data.encode('utf-8')
    elif isinstance(data, collections.Mapping):
        return dict(map(unicode2str, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(unicode2str, data))
    else:
        return data


def escape_wildcard(string):
    """ Escape wildcard for database condition.
    """
    try:
        return string.replace('\\', '\\\\').replace('%', '\%').replace('_', '\_')
    except Exception, e:
        return string
