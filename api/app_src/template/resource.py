"""Routing class
"""
from framework.base_resource import Resource
from framework.err import RequestError


class RESOURCE(Resource):
    """Routing class
    """
    def GET(self, url, params, request, response):
        """HTTP GET
        """
        raise RequestError(http_status=404)

    def PUT(self, url, params, request, response):
        """HTTP PUT
        """
        raise RequestError(http_status=404)

    def POST(self, url, params, request, response):
        """HTTP POST
        """
        raise RequestError(http_status=404)

    def DELETE(self, url, params, request, response):
        """HTTP DELETE
        """
        raise RequestError(http_status=404)
