"""Routing class
"""
from framework.base_resource import CachedRouter, Resource, ResourceRouter
from karaokes_model import KaraokesModel
from karaokes_view import KaraokesView


class KaraokesResource(Resource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = KaraokesModel()
        self.view_instance = KaraokesView()

        self.GET = CachedRouter(  # Replace GET method.
            exe_insts = {  # Register Model.
                '/': self.model_instance.get_karaokes,
                'covers': self.model_instance.get_covers,
                'metadata': self.model_instance.get_metadata
            },
            disp_insts = {  # Register View.
                '/': self.view_instance.karaokes_view
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
