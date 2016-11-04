"""Routing class
"""
from framework.base_resource import RawResource, ResourceRouter
from files_model import FilesModel
# from files_view import FilesView


class FilesResource(RawResource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = FilesModel()
        # self.view_instance = FilesView()

        self.GET = ResourceRouter(
            exe_insts = {  # Register Model.
                'addon': self.model_instance.get_addon,
                'addon_version': self.model_instance.get_addon_version
            },
            disp_insts = {
            }
        )

        self.POST = ResourceRouter(
                exe_insts = {
                    'addon': self.model_instance.upload_addon
                },
                disp_insts = {
                }
            )

        self.DELETE = ResourceRouter(
                exe_insts = {
                    'addon': self.model_instance.delete_addon
                },
                disp_insts = {
                }
            )
