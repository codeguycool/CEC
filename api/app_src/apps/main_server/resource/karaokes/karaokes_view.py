"""View class
"""
from views.content_format import c_karaoke


class KaraokesView:

    def karaokes_view(self, resp):
        resp.update({
            'karaokes': [c_karaoke(row, resp.model_data['content'], detail=resp.model_data['detail']) for row in resp.model_data['metadata']]
        })

        # add update_time for song list.
        if resp.model_data['metadata'] and resp.model_data['metadata'][0].has_key('list_udate'):
            resp['update_time'] = str(resp.model_data['metadata'][0]['list_udate']).split(' ')[0]

        return resp
