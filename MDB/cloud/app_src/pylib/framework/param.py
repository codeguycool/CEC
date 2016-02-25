# -*-coding: utf-8 -*-
'''
Tools for getting request parameter.
'''
from ast import literal_eval
from json import loads

# app module
from framework.err import ERR_REQUEST_ARG, RequestError
from framework.py_utilities import NotSet


def param2int(string, default=None):
    ''' Number string cast to integer.
    '''
    if not string:
        return default
    if not isinstance(string, basestring):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a string'))
    if not string.isdigit():
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a number'))
    return int(string)

def param2limit(string, default=None):
    ''' Number string cast to integer.
    '''
    if string == '-1':
        return -1
    return param2int(string, default)

def param2float(string, default=None):
    ''' Number string cast to float.
    '''
    if not string:
        return default
    if not isinstance(string, basestring):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a string'))
    try:
        return float(string)
    except ValueError:
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a float number'))

def paramNum2bool(string, default=None):
    ''' Number string cast to boolean.
    Args:
        string: "0" is False; biger than 0 is True.
    '''
    if not string:
        return default
    return bool(param2int(string, default))

def _eval_cast(string):
    if not isinstance(string, basestring):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a string'))
    try:
        return literal_eval(string)
    except:
        raise RequestError(ERR_REQUEST_ARG, str_data=('content error'))

def param2bool(string, default=None):
    ''' Boolean string cast to boolean.
    Args:
        string: "True" or "False"
    '''
    if not string:
        return default

    ret = _eval_cast(string)

    if not isinstance(ret, bool):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a bool'))
    return ret

def param2list(string, default=None):
    ''' List format string cast to list.
    '''
    if not string:
        return default

    ret = _eval_cast(string)

    if not isinstance(ret, list):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a list'))
    return ret

def param2dict(string, default=None):
    ''' Dictionary format string cast to dict.
    '''
    if not string:
        return default

    ret = _eval_cast(string)

    if not isinstance(ret, dict):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a dict'))
    return ret

def param2json(string, default=None, check_type=None):
    ''' Json format string cast to dict.
    '''
    if not string:
        return default

    if not isinstance(string, basestring):
        raise RequestError(ERR_REQUEST_ARG, str_data=('not a string'))
    try:
        ret = loads(string)

        if check_type:
            if not isinstance(string, check_type):
                raise RequestError(ERR_REQUEST_ARG, str_data=('format error'))
        return ret
    except RequestError:
        raise
    except:
        raise RequestError(ERR_REQUEST_ARG, str_data=('content error'))


# Parameter class
class Parameters(dict):
    ''' To strengthen params of cheerypy.
    '''
    def get_wtih_default(param2something):
        def param_getter(self, key, default=NotSet, default_s=NotSet, default_r=NotSet, **kwargs):
            ''' Get value by given key with default value.

            [Arguments]
                default   : any object.(optional)
                    Default return value be used if key not found.

                default_s : any object.(optional)
                    Default input parameter string be used if key not found.

                default_r : any object.(optional)
                    Default return value be used if any exception raised.
                    For necessary parameter even input wrong content.
            '''
            try:
                if not self.has_key(key):
                    if default is not NotSet:
                        return default
                    elif default_s is not NotSet:
                        value = default_s
                    raise ValueError('parameter not found')
                else:
                    value = self.get(key)

                    if value is u'': # value is empty string
                        if default is not NotSet:
                            return default

                return param2something(self, string=value, **kwargs)
            except RequestError, e:
                e.str_data = "'%s': %s" % (key, e.str_data)
                raise
            except Exception, e:
                if default_r is not NotSet:
                    return default_r
                #TODO: log
                raise
        return param_getter

    @get_wtih_default
    def get_string(self, string):
        return string

    @get_wtih_default
    def get_int(self, string):
        return param2int(string)

    @get_wtih_default
    def get_float(self, string):
        return param2float(string)

    @get_wtih_default
    def get_limit(self, string):
        return param2limit(string)

    @get_wtih_default
    def get_Nbool(self, string):
        return paramNum2bool(string)

    @get_wtih_default
    def get_bool(self, string):
        return param2bool(string)

    @get_wtih_default
    def get_list(self, string):
        return param2list(string)

    @get_wtih_default
    def get_dict(self, string):
        return param2dict(string)

    @get_wtih_default
    def get_json(self, string, check_type=None):
        return param2json(string, check_type)
