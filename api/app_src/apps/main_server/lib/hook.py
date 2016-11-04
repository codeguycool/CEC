# -*-coding: utf-8 -*-

# 3rd
import cherrypy


class HookCollection(object):
    """A collection for all hooks
    """
    def authenticate(self, request=cherrypy.request):
        """Authenticate
        """
        pass

    def check_privacy(self, response=cherrypy.response):
        """Check privacy
        """
        pass
