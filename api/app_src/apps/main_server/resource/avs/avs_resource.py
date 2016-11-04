"""Routing class
"""
from avs_model import AVsModel
from avs_view import AVsView
from framework.base_resource import CachedRouter, Resource, ResourceRouter


class AVsResource(Resource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = AVsModel()
        self.view_instance = AVsView()

        self.GET = CachedRouter(  # Replace GET method.
            exe_insts = {  # Register Model.
                '/': self.model_instance.get_avs,
                'metadata': self.model_instance.get_metadata
            },
            disp_insts = {  # Register View.
                '/': self.view_instance.avs_view
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
