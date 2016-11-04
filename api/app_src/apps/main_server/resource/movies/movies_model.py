"""Model class
"""

# std
from datetime import datetime
from uuid import uuid4

# app module
from app_var import MAX_RESPONSE_ROWS
from accessor.movies import get_movies_content, lang2source, source2lang
from api.const import REQUEST_POPLAR, REQUEST_LATEST, USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY
from api.tools import UA2field
from framework.db_client.pg_client import PGClient
from framework.err import ERR_DB_NOT_FOUND, ERR_REQUEST_ARG, RequestError
from framework.response import Response


class MoviesModel:

    def get_movies(self, url, params, request, response):
        """ Get movies information.

        [API]
            1) GET RESOURCE/${MOVIE_ID}
                Get target movie detail information.

            2) GET RESOURCE?type=${TYPE}
                Get custom information.

            3) GET RESOURCE
                Get all movie information.

        [Arguments]
            url[0] : string.
                Movie ID to find.
            type   : string.
                Information type.
            since  : int string.
                Response data start from.
            limit  : int string.
                Number of response rows to display.
            lang  : string.
                To choose display content.
        """
        # API args
        movie_id = url[0] if len(url) else None
        request_type = params.get_string('type', REQUEST_LATEST)
        since = params.get_int('since', None)
        lang = params.get_string('lang', None)

        table = 'movies'
        fields = None
        condition = ['source=%(source)s', {'source': lang2source(lang)}]
        ordering_sql = None

        if movie_id:  # Get one moive information
            limit = 0
            condition = ['id=%(id)s', {'id': movie_id}]

        elif request_type:
            limit = params.get_limit('limit', 20)

            constraint_sql = """title!='' AND (posterurl is not null OR thumbnailurl is not null) AND
                directors!='{}' AND writers!='{}' AND stars!='{}' AND description is not null"""
            condition[0] = '%s AND %s' % (condition[0], constraint_sql)

            if request_type == REQUEST_POPLAR:  # Get popular moive information
                ordering_sql = "ORDER BY total_count DESC NULLS LAST, releasedate->>'Default' DESC NULLS LAST"
                
            elif request_type == REQUEST_LATEST:  # Get latest moive information
                table = 'movies, movie_latest'
                condition[0] = 'movies.imdbid = movie_latest.imdbid AND %s' % condition[0]
                ordering_sql = 'ORDER BY movie_latest.rdate DESC'
            else:
                raise RequestError(ERR_REQUEST_ARG, str_data=('type.'))
            
        else:  # Get all moive information
            limit = params.get_limit('limit', 20)
            ordering_sql = 'ORDER BY year DESC'

        db_inst = PGClient()

        else_sql = '%s %s %s' % (
            ordering_sql if ordering_sql else '',
            'OFFSET %s' % since if since else '',
            'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
        )

        movies, rowcount = db_inst.query(table=table, fields=fields, condition=condition, ret_type='all', else_sql=else_sql)

        if not rowcount and movie_id:
            raise RequestError(http_status=404)

        content = get_movies_content(movies_row=movies, db_inst=db_inst)

        return Response(model_data={
            'metadata': movies,
            'content': content,
            'detail': True if movie_id else False
        })

    def add_count(self, url, params, request, response):
        """ Add user action count of choosen movie.

        [Arguments]
            url[0] : string.
                Movie ID.
            type   : string.
                Action type.
        """
        # API args
        movie_id = url[0] if len(url) else None
        action_type = params.get_string('type', None)

        if not action_type or action_type not in [USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY]:
            raise RequestError(ERR_REQUEST_ARG, str_data=('type error.'))

        db_inst = PGClient()

        cur, rowcount = db_inst.query(table='movies', condition=['id=%(id)s', {'id': movie_id}])
        if not rowcount:
            raise RequestError(ERR_DB_NOT_FOUND)
        movie_data = cur.fetchone()
   
        count, total = self._add_user_action(
            action_type=action_type, movie_id=movie_id, imdb_id=movie_data['imdbid'], db_inst=db_inst
        )

        db_inst.commit()

        return Response(content={
            'count': count,
            'total': total
        })

    def _add_user_action(self, action_type, movie_id, imdb_id, db_inst):
        # record user action
        cur = db_inst.insert(table='movie_statistics', data={
            'id': str(uuid4()),  # FIXME if we want use time uuid.
            'movieid': movie_id,
            'imdbid': imdb_id,
            'type': action_type[0],
            'datetime': datetime.utcnow().isoformat()
        })

        # update count.
        sql = """
            UPDATE    movies SET %(count_filed)s=%(count_filed)s+1, total_count=total_count+1
            WHERE     %(id_field)s='%(id)s' 
            RETURNING %(count_filed)s, total_count""" % {
            'count_filed': UA2field(action_type),
            'id_field': 'imdbid' if imdb_id else 'id',
            'id': imdb_id if imdb_id else movie_id
        }
        cur = db_inst.execute(cmd=sql)

        return cur.fetchone()

    def get_movie_titles(self, url, params, request, response):
        """ Get movie titles of each source.

        [Arguments]
            url[0] : string.
                IMDB ID.
        """
        # API args
        if not url:
            raise RequestError(ERR_REQUEST_ARG, str_data=('format error.'))
        imdbid = url[0]

        db_inst = PGClient()

        condition = ['imdbid = %(imdbid)s', {'imdbid': imdbid}]
        rows, rowcount = db_inst.query(table='movies', fields=['source, title'], condition=condition, ret_type='all')

        return Response(
            content={
                'titles': {
                    source2lang(row['source']): row['title'] for row in rows if source2lang(row['source']) is not None
                }
            }
        )

    def get_metadata(self, url, params, request, response):
        """ Use movie id of any source to get all metadata.
        [Arguments]
            ids : list string.
                IDs of movies to get metadata.
        """
        # API args
        ids = params.get_list('ids', None)
        if not ids:
            raise RequestError(ERR_REQUEST_ARG, str_data=('ids.'))

        resp = Response(content={'movies': {}})

        db_inst = PGClient()

        # Get items with ids
        condition = ['id IN %(id)s', {'id': tuple(ids)}]
        movies, rowcount = db_inst.query(table='movies', condition=condition, ret_type='all')

        for movie in movies:
            resp['movies'][movie['id']] = {'imdbid': movie['imdbid'], 'metadata': {}}

            # Get metadata of each source.
            if movie['imdbid']:
                condition = ['imdbid = %(imdbid)s', {'imdbid': movie['imdbid']}]
                rows, rowcount = db_inst.query(table='movies', condition=condition, ret_type='all')
            else:
                rows = [movie]

            for row in rows:
                resp['movies'][movie['id']]['metadata'][row['source']] = {
                    'id': row['id'],
                    'source': row['source'],
                    'title': row['title'],
                    'akas': row['akas'],
                    'genres': row['genres'],
                    'rating': row['rating'],
                    'posterurl': row['posterurl'],
                    'directors': row['directors'],
                    'stars': row['stars'],
                    'releasedate': row['releasedate'],
                    'countries': row['countries'],
                    'description': row['description'],
                    'url': row['url'],
                    'md5sum': row['md5sum'],
                    'thumbnailurl': row['thumbnailurl']
                }

        # patch up not found data.
        for missing_id in set(ids).difference(resp['movies'].keys()):
            resp['movies'][missing_id] = {}

        return resp
