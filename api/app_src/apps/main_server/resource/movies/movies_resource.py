"""Routing class
"""
# app module
from framework.base_resource import CachedRouter, Resource, ResourceRouter
from movies_model import MoviesModel
from movies_view import MoviesView


class MoviesResource(Resource):
    """Routing class
    """
    def __init__(self):
        self.model_instance = MoviesModel()
        self.view_instance = MoviesView()

        self.GET = CachedRouter(
            exe_insts = {
                '/': self.model_instance.get_movies,
                'titles': self.model_instance.get_movie_titles,
                'metadata': self.model_instance.get_metadata
            },
            disp_insts = {
                '/': self.view_instance.movie_view
            },
            cache_all = True
        )

        self.POST = ResourceRouter(
            exe_insts = {
                'count': self.model_instance.add_count
            },
            disp_insts = {
            }
        )
