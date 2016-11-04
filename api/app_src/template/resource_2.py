"""Routing class
"""
from framework.base_resource import Resource, ResourceRouter


class RESOURCE(Resource):
    """Routing class
    """
    def __init__(self):
        # Sample code.
        self.model_instance = MODEL()
        self.view_instance = VIEW()

        self.GET = ResourceRouter(  # Replace GET method.
            exe_insts = {  # Register Model.
                '/': self.model_instance.root,  # root resource.
                'api': self.model_instance.get_api,
                'api_2': self.model_instance.get_api_2
            },
            disp_insts = {  # Register View.
                '/': self.view_instance.root,
                'api': self.view_instance.get_api_view
            }
        )
