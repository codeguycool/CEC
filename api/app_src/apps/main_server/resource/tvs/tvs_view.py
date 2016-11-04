"""View class
"""
from views.content_format import c_tv


class TVsView:

    def TVs_view(self, resp):
        resp.update({
            'tvs': [c_tv(row, detail=resp.model_data['detail']) for row in resp.model_data['data']]
        })

        return resp

    def play_list_view(self, resp):

        resp.update({
            # first element is None if no data
            'play_list': resp.model_data['data'][0] if resp.model_data['data'][0] else []
        })

        return resp
