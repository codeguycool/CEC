'''Routing class
'''
# app module
from framework.base_resource import Resource, ResourceRouter
from movies_model import MoviesModel
from movies_view import MoviesView


class MoviesResource(Resource):
    '''Routing class
    '''
    def __init__(self):
        self.model_instance = MoviesModel()
        self.view_instance = MoviesView()

        self.GET = ResourceRouter(
            exe_insts = {
                '/' : self.model_instance.get_movies
            },
            disp_insts = {
                '/' : self.view_instance.movie_view
            }
        )

