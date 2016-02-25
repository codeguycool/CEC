'''Model class
'''
# app module
from framework.err import ERR_DB_NOT_FOUND, ERR_REQUEST_ARG, RequestError
from framework.response import Response
from framework.sys_const import LANG_ENG, LANG_SCH, LANG_TCH, DB_SRC_ATMOVIES, DB_SRC_DOUBAN, DB_SRC_IMDB
from db_client.pg_client import PGClient


class MoviesModel:

    def get_movies(self, url, params, request, response):
        ''' Get movies information.

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
        '''
        # API args
        movie_id = url[0] if len(url) else None
        request_type = params.get_string('type', None)
        since = params.get_int('since', None)
        lang = params.get_string('lang', None)

        fields = None
        condition = ['source=%(source)s', {'source': self.lang2source(lang)}]
        ordering_sql = None

        if movie_id: # Get one moive information
            limit = params.get_limit('limit', None)
            condition = ['id=%(id)s', {'id': movie_id}]

        elif request_type:
            limit = params.get_limit('limit', 20)

            constraint_sql = """title!='' AND posterurl is not null AND directors!='{}' AND
                writers!='{}' AND stars!='{}' AND description is not null"""
            condition[0] = '%s AND %s' % (condition[0], constraint_sql)

            if request_type == "popular": # Get popular moive information
                fields = ['*', 'vcount+dcount+pcount AS total_count']
                ordering_sql = 'ORDER BY total_count DESC NULLS LAST'
                
            elif request_type == "latest": # Get latest moive information
                ordering_sql = 'ORDER BY year DESC'
            else:
                raise RequestError(ERR_REQUEST_ARG, str_data=('type.'))
            
        else: # Get all moive information
            limit = params.get_limit('limit', 20)
            ordering_sql = 'ORDER BY year DESC'

        #TODO: cache data
        db_inst = PGClient()

        else_sql = '%s %s %s' % (
            ordering_sql if ordering_sql else '',
            'OFFSET %s' % since if since else '',
            'LIMIT %s' % limit if limit else ''
        )

        movies, rowcount = db_inst.query(table='movie', fields=fields, condition=condition, ret_type='all', else_sql=else_sql)

        if not rowcount and movie_id:
            return Response(success=False, err_code=ERR_DB_NOT_FOUND)

        content = self.get_movies_content(movies_row=movies, db_inst=db_inst)

        return Response(model_data={
            'metadata': movies,
            'content': content,
            'detail': True if movie_id else False
        })

    def get_movies_content(self, movies_row, db_inst=None):
        ''' Get movies content by imdb id from given row data.
        [Arguments]
            movies_row : list.
                Movie rows data.
            db_inst    : DB client instance.
                Set for reuse client.

        [Return]
            content: dict
                Movie content row data with key is imdb id.
        '''
        if not db_inst:
            db_inst = PGClient()

        id_sqls = []
        for row in movies_row:
            imdb_id = row.get('imdbid', None)
            if imdb_id:
                id_sqls.append("imdbid='%s'" % imdb_id)

        if not id_sqls:
            return {}

        cond_sql = "source='tudou' AND (%s)" % ' OR '.join(id_sqls)
        content, rowcount = db_inst.query(table='moviecontent', condition=[cond_sql], ret_type='all')

        return {row['imdbid']:row for row in content}

    def lang2source(self, lang):
        ''' Mapping language type to movie source.
        '''
        return {
            LANG_ENG: DB_SRC_IMDB,
            LANG_SCH: DB_SRC_DOUBAN,
            LANG_TCH: DB_SRC_ATMOVIES
        }.get(lang, DB_SRC_IMDB)

