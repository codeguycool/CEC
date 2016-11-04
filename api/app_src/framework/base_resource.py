# 3rd party library
import cherrypy

# app module
from framework.cache import Cache
from framework.err import ERR_MSG, RequestError
from framework.param import Parameters
from framework.py_utilities import NotSet
from framework.response import Response
from framework.sys_var import ALLOW_HTTP_METHOD


class ResourceDispatcher(object):
    """Super class of RESTful interface.
    """
    def default(self, *vpath, **params):
        """Dispatcher
        """
        try:
            method = getattr(self, cherrypy.request.method, None)
            if not method:
                cherrypy.response.headers["Allow"] = ",".join(ALLOW_HTTP_METHOD)
                raise RequestError(http_status=405)

            response = method(vpath, Parameters(params), cherrypy.request, cherrypy.response)
            if isinstance(response, Response) and not response.is_success():
                cherrypy.response.status = response.http_status
            return response
        except:
            raise 


class Resource(ResourceDispatcher):
    """Base class for providing a RESTful interface to a resource (Return JSON Data)
    """
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def default(self, *vpath, **params):
        return super(Resource, self).default(*vpath, **params)


class RawResource(ResourceDispatcher):
    """Base class for providing a RESTful interface to a resource (Return RAW Data)
    """
    @cherrypy.expose
    def default(self, *vpath, **params):
        return super(RawResource, self).default(*vpath, **params)


class ResourceRouter(object):
    """API router for Resource instanse. Base on Model 2.

    Reference to template/resource_2.py
    """
    def __init__(self, exe_insts, disp_insts):
        """
        [Arguments]
            exe_insts  : dict.
                Setting of Model. 

                [Format]
                    {
                        "API_NAME": EXE_INST
                    }

            disp_insts  : dict.
                Setting of View. 

                [Format]
                    {
                        "API_NAME": DISP_INST
                    }
        """
        self.exe_insts = exe_insts
        self.disp_insts = disp_insts

    def parse_url(self, url):
        """ Get API key from cherrypy URL path.
        """
        cmd = '/'  # Define for resource root path.
        if url and url[0] in self.exe_insts:
            cmd = url[0]  # Only take first level of url to match exe_insts key.
            url = url[1:]
        return cmd, url

    def __call__(self, url, params, request, response):  # router
        cmd, url_args = self.parse_url(url)

        # Model part
        exe_inst = self.exe_insts.get(cmd, None)

        if not exe_inst:
            raise RequestError(http_status=404)

        resp_inst = exe_inst(url_args, params, request, response)

        # Just return Response when it is not success.
        if isinstance(resp_inst, Response) and not resp_inst.is_success():
            return resp_inst

        # View part
        disp_inst = self.disp_insts.get(cmd, None)

        if not disp_inst:  # Retuen Response when not define its View.
            return resp_inst

        v_ret = disp_inst(resp_inst)

        return v_ret


class CachedRouter(ResourceRouter):
    """ Cache API response.
    """
    def __init__(self, exe_insts, disp_insts, cache_list=NotSet, cache_all=False):
        """
        [Arguments]
            cache_list  : list.
                Custom API keys to enable cache.

                [Format]
                    ['API_KEY_1', 'API_KEY_2', ...]
                    Value of key has to set the same as in exe_insts.

                [Example]
                    ['/', 'movies']

            cache_all   : bool.
                Cache all APIs.
        """
        super(CachedRouter, self).__init__(exe_insts, disp_insts)

        if cache_all:
            self.cache_list = self.exe_insts.keys()
        elif cache_list is NotSet:
            self.cache_list = []
        else:
            self.cache_list = cache_list

    def __call__(self, url, params, request, response):
        cmd, url_args = self.parse_url(url)

        # Check this API is enable cache.
        if cmd in self.cache_list:
            cache = Cache()
        else:
            cache = None

        # Get value from Cache if this API is cached.
        if cache:
            cache_ret = cache.get_by_request(request)
            if cache_ret:  # reutrn value if cache hit
                return cache_ret

        api_ret = super(CachedRouter, self).__call__(url, params, request, response)

        if isinstance(api_ret, Response) and not api_ret.is_success():
            return api_ret  # Not cache faild response.
                            # If you want cache this, you have to recover data to Response object,
                            # to ensure response correct http status code.

        # Cache response with request information (cache miss).
        if cache:
            cache.set_by_request(request, api_ret)

        return api_ret
