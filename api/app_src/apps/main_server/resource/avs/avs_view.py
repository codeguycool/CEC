"""View class
"""
from views.content_format import c_av


class AVsView:

    def avs_view(self, resp):
        resp.update({
            'avs': [c_av(row, detail=resp.model_data['detail']) for row in resp.model_data['metadata']]
        })

        return resp
