'''Routing class
'''
from framework.base_resource import Resource


class RESOURCE(Resource):
    '''Routing class
    '''
    def GET(self, url, params, request, response):
        '''HTTP GET
        '''
        raise HTTPError(404)

    def PUT(self, url, params, request, response):
        '''HTTP PUT
        '''
        raise HTTPError(404)

    def POST(self, url, params, request, response):
        '''HTTP POST
        '''
        raise HTTPError(404)

    def DELETE(self, url, params, request, response):
        '''HTTP DELETE
        '''
        raise HTTPError(404)
