"""Routing class
"""
from framework.base_resource import CachedRouter, Resource
from search_model import SearchModel
from search_view import SearchView


class SearchResource(Resource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = SearchModel()
        self.view_instance = SearchView()

        self.GET = CachedRouter(  # Replace GET method.
            exe_insts = {  # Register Model.
                '/': self.model_instance.search_media,
                'index': self.model_instance.search_index,
                'keywords': self.model_instance.suggest_keyword
            },
            disp_insts = {  # Register View.
                '/': self.view_instance.search_view,
            },
            cache_all = True
        )
