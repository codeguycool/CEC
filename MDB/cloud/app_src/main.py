#!/usr/bin/python
''' Main class of could server.
'''
import json
import os
from sys import exc_info as _exc_info, path as sys_path 

import cherrypy
#import uwsgi

#Sys.path area
sys_path.append('{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'pylib'))
sys_path.append('{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'resource'))

from framework.err import ERR_MSG, RequestError
from framework.hook import HookCollection
from framework.response import Response


#Function area
hooks = HookCollection()
def onStartResource():
    '''Hook function before processing request
    '''
    #hooks.authenticate()

def onEndResource():
    '''Hook function before sending response
    '''
    #hooks.check_privacy()


def handle_error():
    '''
    Note:
        Not catch Httpd code 3XX~4XX exception. These exception will just response to client. 
    '''
    excpetion_inst = _exc_info()[1]

    if isinstance(excpetion_inst, RequestError):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cherrypy.response.status = 200
        resp = Response(success=False, err_code=excpetion_inst.code, err_msg=excpetion_inst.get_msg())
        cherrypy.response.body = json.dumps(resp)
    else: # hide exception information
        cherrypy.response.show_tracebacks = False
        cherrypy.response.status = 500
        cherrypy.response.body = [
            "<html><body>%s</body></html>" % ERR_MSG[500]
        ]
        #print excpetion_inst.get_msg()


#Class area
class mainApp(object):
    '''The main class for the whole framework
    '''
    _cp_config = {'request.error_response': handle_error}


#Resource area
root = mainApp()

from movies.movies_resource import MoviesResource
root.movies = MoviesResource()

#Hook area
cherrypy.tools.onStartResource = cherrypy.Tool('on_start_resource', onStartResource)
cherrypy.tools.onEndResource = cherrypy.Tool('on_end_resource', onEndResource)

application = None

#Running area
if __name__ == "__main__":
    cherrypy.config.update({
        #Development Server Config
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 7777,
        #'environment': 'production'

        #Hook Config
        'tools.onStartResource.on': True,
        'tools.onEndResource.on': True,

        #Log
        #'log.access_file': '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'tmp/logs'),
        #'log.error_file': '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'tmp/logs')
        })
    cherrypy.quickstart(root, '/', None)
else:
    cherrypy.config.update({
        #Hook Config
        'tools.onStartResource.on': True,
        'tools.onEndResource.on': True,

        #Log
        'log.access_file': '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'tmp/logs'),
        'log.error_file': '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'tmp/logs'),

        #WSGI
        'environment': 'embedded'
        })
    application = cherrypy.Application(root, script_name='', config=None)
    #uwsgi.applications = {'app':application}
