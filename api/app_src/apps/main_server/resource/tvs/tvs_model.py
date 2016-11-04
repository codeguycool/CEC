"""Model class
"""

# std
from datetime import datetime
from uuid import uuid4

# app module
from app_var import MAX_RESPONSE_ROWS
from accessor.tvs import gen_fetch_dramas_sql, lang2source
from api.const import REQUEST_POPLAR, REQUEST_LATEST, USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY
from api.tools import UA2field
from framework.db_client.pg_client import PGClient
from framework.err import ERR_DB_NOT_FOUND, ERR_REQUEST_ARG, RequestError
from framework.response import Response


class TVsModel:

    def allow_display_play_source(self):
        return [
            'dailymotion',
            'googledrive',
            'youtube'
        ]

    def sql_array_string(self):
        return '{%s}' % ','.join(self.allow_display_play_source())

    def get_TVs(self, url, params, request, response):
        """ Get TVs information.

        [API]
            1) GET RESOURCE/${DRAMA_ID}
                Get target dramas detail information.

            2) GET RESOURCE?type=${TYPE}
                Get custom information.

        [Arguments]
            url[0] : string.
                Drama ID to find.
            since  : int string.
                Response data start from.
            limit  : int string.
                Number of response rows to display.
            lang  : string.
                To choose display content.
            drama_kind  : int string.
                To choose kind of dramas.
            type   : string.
                The type to display information.
        """
        # API args
        drama_id = url[0] if len(url) else None
        request_type = params.get_string('type', REQUEST_LATEST)
        since = params.get_int('since', None)
        lang = params.get_string('lang', None)

        condition_sql = ''
        condition_data = {}
        ordering_sql = None

        if drama_id:  # Get one drama information
            limit = 0
            condition_sql = 'id=%(id)s'
            condition_data = {'id': drama_id}

        else:  # Get drama list information
            limit = params.get_limit('limit', 20)

            kind = params.get_int('drama_kind', 1)
            if kind not in xrange(0, 9):
                raise RequestError(ERR_REQUEST_ARG, str_data=('drama_kind.'))

            condition_sql = "kind='%s'" % kind
            condition_sql = "%s AND source='%s'" % (condition_sql, lang2source(lang))
            condition_sql = "%s AND '%s' && ARRAY(SELECT json_object_keys(play_urls))" % (
                condition_sql, self.sql_array_string()
            )

            if request_type == REQUEST_POPLAR:  # Get popular drama information
                ordering_sql = "ORDER BY total_count DESC NULLS LAST, rdate DESC NULLS LAST"
                
            elif request_type == REQUEST_LATEST:  # Get latest drama information
                ordering_sql = 'ORDER BY rdate DESC NULLS LAST'
            else:
                raise RequestError(ERR_REQUEST_ARG, str_data=('type.'))

        dramas_sql = u'''
            SELECT *
            FROM   drama
            WHERE  {0}
            {1} {2} {3}
        '''.format(
            condition_sql,
            ordering_sql if ordering_sql else '',
            'OFFSET %s' % since if since else '',
            'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
        )     

        db_inst = PGClient()

        cur = db_inst.execute(cmd=gen_fetch_dramas_sql(dramas_sql=dramas_sql), data=condition_data)

        if not cur.rowcount and drama_id:
            raise RequestError(http_status=404)

        return Response(model_data={
            'data': cur.fetchall(),
            'detail': False if drama_id else True
        })

    def get_play_list(self, url, params, request, response):
        """ Get play list.

        [Arguments]
            url[0] : string.
                Drama ID.
            source :
                Video source.
            since  : int string.
                Response rows start from.
            limit  : int string.
                Number of response rows to display.
        """
        # API args
        drama_id = url[0] if len(url) else None
        source = params.get_string('source', None)
        since = params.get_int('since', 0)
        limit = params.get_limit('limit', 30)

        if not drama_id:
            raise RequestError(http_status=404)

        condition = ['id=%(id)s', {'id': drama_id}]

        if source in self.allow_display_play_source():
            fields = ['''
                (
                    ARRAY(SELECT json_array_elements(play_urls->'%s'))
                )[%s:%s] AS play_list
            ''' % (
                    source,
                    since+1 if since > 0 else 1,
                    limit+since if limit > 0 else "json_array_length(play_urls->'%s')" % source  # limit it if need.
                )
            ]
        else:
            raise RequestError(ERR_REQUEST_ARG, str_data=('source.'))

        db_inst = PGClient()

        dramas, rowcount = db_inst.query(table='drama', fields=fields, condition=condition, ret_type='all')

        if not rowcount:
            raise RequestError(http_status=404)

        return Response(model_data={
            'data': dramas[0]
        })

    def add_count(self, url, params, request, response):
        """ Add user action count of choosen dramas.

        [Arguments]
            url[0] : string.
                Drama ID.
            type   : string.
                Action type.
        """
        # API args
        drama_id = url[0] if len(url) else None
        action_type = params.get_string('type', None)

        if not action_type or action_type not in [USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY]:
            raise RequestError(ERR_REQUEST_ARG, str_data=('type error.'))

        db_inst = PGClient()

        cur, rowcount = db_inst.query(table='drama', condition=['id=%(id)s', {'id': drama_id}])
        if not rowcount:
            raise RequestError(ERR_DB_NOT_FOUND)
   
        count, total = self._add_user_action(action_type=action_type, drama_id=drama_id, db_inst=db_inst)

        db_inst.commit()

        return Response(content={
            'count': count,
            'total': total
        })

    def _add_user_action(self, action_type, drama_id, db_inst):
        # record user action
        cur = db_inst.insert(table='drama_statistics', data={
            'id': str(uuid4()),  # FIXME if we want use time uuid.
            'dramaid': drama_id,
            'type': action_type[0],
            'datetime': datetime.utcnow().isoformat()
        })

        # update count.
        sql = """
            UPDATE    drama SET %(filed)s=%(filed)s+1, total_count=total_count+1
            WHERE     id='%(id)s' 
            RETURNING %(filed)s, total_count""" % {
            'filed': UA2field(action_type), 'id': drama_id
        }
        cur = db_inst.execute(cmd=sql)

        return cur.fetchone()


    def get_metadata(self, url, params, request, response):
        """ Use TV id of any source to get all metadata.
        [Arguments]
            ids : list string.
                IDs of TVs to get metadata.
        """
        # API args
        ids = params.get_list('ids', None)
        if not ids:
            raise RequestError(ERR_REQUEST_ARG, str_data=('ids.'))

        resp = Response(content={'tvs': {}})

        db_inst = PGClient()

        # Get items with ids
        condition = ['id IN %(id)s', {'id': tuple(ids)}]
        tvs, rowcount = db_inst.query(table='drama', condition=condition, ret_type='all')

        for tv in tvs:
            resp['tvs'][tv['id']] = {'dbid': tv['dbid'], 'metadata': {}}

            # Get metadata of each source.
            if tv['dbid']:
                condition = ['dbid = %(id)s', {'id': tv['dbid']}]
                rows, rowcount = db_inst.query(table='drama', condition=condition, ret_type='all')
            else: # only one record
                rows = [tv]

            for row in rows:
                resp['tvs'][tv['id']]['metadata'][row['source']] = {
                    'id': row['id'],
                    'source': row['source'],
                    'title': row['title'],
                    'akas': row['akas'],
                    'kind': row['kind'],
                    'genres': row['genres'],
                    'posterurl': tv['posterurl'],
                    'stars': row['stars'],
                    'year': row['year'],
                    'region': row['region'],
                    'description': row['description'],
                    'url': row['url'],
                    'update_eps': row['update_eps'],
                    'total_eps': row['total_eps'],
                    'completed': row['completed'],
                    'md5sum': row['md5sum']
                }

        # patch up not found data.
        for missing_id in set(ids).difference(resp['tvs'].keys()):
            resp['tvs'][missing_id] = {}

        return resp

