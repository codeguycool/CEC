# app module
from framework.base_resource import Resource, ResourceRouter, CachedRouter
from dbsync_model import DbSyncModel
from dbsync_view import DbSyncView


class DbSyncResource(Resource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = DbSyncModel()
        self.view_instance = DbSyncView()

        self.GET = CachedRouter(
            exe_insts={
                'last_timestamp': self.model_instance.get_last_timestamp,
                'task_status': self.model_instance.get_task_status,
                'patch_columns': self.model_instance.get_patch_columns
            },
            disp_insts={
                'last_timestamp': self.view_instance.timestamp,
                'task_status': self.view_instance.task_done,
                'patch_columns': self.view_instance.columns
            }
        )

        self.POST = ResourceRouter(
            exe_insts={
                'patch_data': self.model_instance.patch_data
            },
            disp_insts={
                'patch_data': self.view_instance.message
            }
        )

        self.PUT = ResourceRouter(
            exe_insts={
                'update_latest_movies': self.model_instance.update_latest_movies,
                'rebuild_keyword': self.model_instance.rebuild_keyword
            },
            disp_insts={
                'update_latest_movies': self.view_instance.rowcount,
                'rebuild_keyword': self.view_instance.message
            }
        )
