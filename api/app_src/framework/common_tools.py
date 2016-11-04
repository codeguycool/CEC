# -*-coding: utf-8 -*-
"""Common function
"""

# std
import collections
import os

# 3rd party
import cherrypy
from cherrypy._cpcompat import json_encode

# app module
from framework.sys_const import LOG_WARNING
from framework.sys_tools import log


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


def streaming_generator(iter_data, file_name=None):
    """ Return a generator for streaming a file.

    [Arguments]
        iter_data : iterator
            Iterat orobject of output data.
        file_name : string (Option)
            File name to save.
    """
    try:
        if file_name:
            return record_content(iter_data, file_name)
        return content(iter_data)
    except Exception, e:
        log.send(LOG_WARNING, str(e))
        raise


def content(iter_data):
    """ Streaming content.

    [Arguments]
        Ref to streaming_generator.
    """
    for chunk in iter_data:
        if chunk:
            yield chunk


def record_content(iter_data, file_name):
    """ Streaming content and save data as a new file.

    [Arguments]
        Ref to streaming_generator.
    """
    tmp_name = '%s_tmp' % file_name
    try:
        # write chunk data and yield chunk data
        with open(tmp_name, 'wb') as f:
            for chunk in iter_data:
                if chunk:
                    yield chunk
                    f.write(chunk)
                    f.flush()
        # if save file success, rename temp file
        os.rename(tmp_name, file_name)
    except IOError:
        # if save file error, yield other chunk data
        for chunk in iter_data:
            if chunk:
                yield chunk

    # remove fail temp file
    if os.path.exists(tmp_name):
        os.remove(tmp_name)


def response_json_out(function):
    """ API response in json format For RawResource.
    Usage:
        Decorate Model/View method. 
    """
    def wrapper(*args, **kwargs):
        request = cherrypy.serving.request

        if request.handler is None:  # reference to json_out of cherrypy.
            return function(*args, **kwargs)

        cherrypy.serving.response.headers['Content-Type'] = 'application/json'

        return json_encode(function(*args, **kwargs))
    return wrapper
