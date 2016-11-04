"""View class
"""
# app module


class DbSyncView:

    def timestamp(self, resp):
        resp.update({
            'timestamp': str(resp.model_data['timestamp']) if resp.model_data['timestamp'] else None
        })

        return resp

    def rowcount(self, resp):
        resp.update({
            'rowcount': resp.model_data['rowcount']
        })

        return resp

    def task_done(self, resp):
        resp.update({
            'task_done': resp.model_data['task_done']
        })

        return resp

    def message(self, resp):
        resp.update({
            'message': resp.model_data['message']
        })

        return resp

    def columns(self, resp):
        resp.update({
            'columns': resp.model_data['columns']
        })

        return resp
