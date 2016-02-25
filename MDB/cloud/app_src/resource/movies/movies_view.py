'''View class
'''
# app module
from views.content_format import c_movie


class MoviesView:
    def movie_view(self, resp):
        resp.update({
            'movies': [c_movie(row, resp.model_data['content'], detail=resp.model_data['detail']) for row in resp.model_data['metadata']]
        })

        return resp

