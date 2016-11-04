#!/usr/bin/python
""" Main class of could server.
"""

# std
import json
import os
from sys import exc_info as _exc_info, path as sys_path 

# 3rd
import cherrypy

# add Sys.path
sys_path.append('{0}/../..'.format(os.path.dirname(os.path.realpath(__file__))))
sys_path.append('{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'lib'))
sys_path.append('{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'resource'))
sys_path.append('{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'background'))

# proj
from dbsync.dbsync_resource import DbSyncResource
from framework.err import ERR_MSG, RequestError
from framework.response import Response


def handle_error():
    """
    Note:
        Not catch Httpd code 3XX~4XX exception. These exception will just response to client. 
    """
    excpetion_inst = _exc_info()[1]

    if isinstance(excpetion_inst, RequestError):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cherrypy.response.status = excpetion_inst.http_status
        resp = Response(success=False, err_code=excpetion_inst.code, err_msg=excpetion_inst.get_msg())
        cherrypy.response.body = json.dumps(resp)
    else:  # hide exception information
        cherrypy.response.show_tracebacks = False
        cherrypy.response.status = 500
        cherrypy.response.body = [
            "<html><body>%s</body></html>" % ERR_MSG[500]
        ]
        # print excpetion_inst.get_msg()


# Class area
class mainApp(object):
    """The main class for the whole framework
    """
    dbsync = DbSyncResource()

# update server config
cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': 7777,
    'server.max_request_body_size': 0,
    'log.access_file': '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'tmp/logs'),
    'log.error_file': '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)), 'tmp/logs'),
    'request.error_response': handle_error
})

# start server
root = mainApp()
cherrypy.quickstart(root, '/')
