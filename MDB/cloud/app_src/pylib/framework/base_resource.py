# 3rd party library
import cherrypy

# app module
from framework.err import ERR_MSG
from framework.param import Parameters
from framework.sys_var import ALLOW_HTTP_METHOD


class Resource(object):
    """Base class for providing a RESTful interface to a resource (Return JSON Data)
    """
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def default(self, *vpath, **params):
        """Dispatcher
        """
        try:
            method = getattr(self, cherrypy.request.method, None)
            if not method:
                cherrypy.response.headers["Allow"] = ",".join(ALLOW_HTTP_METHOD)
                raise cherrypy.HTTPError(405, ERR_MSG[405])
            return method(vpath, Parameters(params), cherrypy.request, cherrypy.response)
        except:
            raise 

    def GET(self, url, params, request, response):
        """ Example. 
        """
        raise cherrypy.HTTPError(404)


class ResourceRouter:
    '''API router for Resource instanse. Base on Model 2.

    Reference to template/resource_2.py
    '''
    def __init__(self, exe_insts, disp_insts):
        '''
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
        '''
        self.exe_insts = exe_insts
        self.disp_insts = disp_insts

    def __call__(self, url, params, request, response):
        cmd = '/' # Define for resource root path.
        if url and url[0] in self.exe_insts:
            cmd = url[0] # Only take first level of url to match exe_insts key.
            url = url[1:]

        exe_inst = self.exe_insts.get(cmd, None)

        if not exe_inst:
            raise cherrypy.HTTPError(404)

        resp_inst = exe_inst(url, params, request, response)

        if not resp_inst['result']['success']: # Just return Response when its success is False.
            return resp_inst

        disp_inst = self.disp_insts.get(cmd, None)

        if not disp_inst: # Retuen Response when not define its View.
            return resp_inst

        v_ret = disp_inst(resp_inst)

        return v_ret

