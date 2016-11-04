"""Routing class
"""
from framework.base_resource import CachedRouter, Resource, ResourceRouter
from tvs_model import TVsModel
from tvs_view import TVsView


class TVsResource(Resource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = TVsModel()
        self.view_instance = TVsView()

        self.GET = CachedRouter(  # Replace GET method.
            exe_insts = {  # Register Model.
                '/': self.model_instance.get_TVs,
                'play_list': self.model_instance.get_play_list,
                'metadata': self.model_instance.get_metadata
            },
            disp_insts = {  # Register View.
                '/': self.view_instance.TVs_view,
                'play_list': self.view_instance.play_list_view
            },
            cache_all = True
        )

        self.POST = ResourceRouter(
            exe_insts = {
                'count': self.model_instance.add_count
            },
            disp_insts = {
            }
        )
