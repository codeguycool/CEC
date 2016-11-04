"""View class
"""
# app module
from views.content_format import c_av, c_movie, c_search_karaoke, c_tv


class SearchView:

    def search_view(self, resp):
        item_pair = {
            'movies': {
                'view': c_movie,  # Instance of item view creater.
                'data': ['content', 'detail']  # Data pass to view instance.
            },
            'karaokes': {
                'view': c_search_karaoke,
                'data': ['detail']
            },
            'avs': {
                'view': c_av,
                'data': ['detail']
            },
            'tvs': {
                'view': c_tv,
                'data': []
            }
        }[resp.model_data['media_type']]

        resp.update({
            'results': [
                item_pair['view'](row, *[resp.model_data[k] for k in item_pair['data']])
                for row in resp.model_data['metadata']
            ]
        })

        return resp
