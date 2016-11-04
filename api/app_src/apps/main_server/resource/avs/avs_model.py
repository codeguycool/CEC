"""Model class
"""

# std
from datetime import datetime
from uuid import uuid4

# app module
from app_var import MAX_RESPONSE_ROWS
from api.const import REQUEST_POPLAR, REQUEST_LATEST, USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY
from api.tools import UA2field
from framework.db_client.pg_client import PGClient
from framework.err import ERR_DB_NOT_FOUND, ERR_REQUEST_ARG, RequestError
from framework.response import Response
from framework.sys_const import DB_SRC_DMM


class AVsModel:

    def get_avs(self, url, params, request, response):
        """ Get AVs information.

        [API]
            1) GET RESOURCE/${AV_ID}
                Get target AVs detail information.

            2) GET RESOURCE?type=${TYPE}
                Get custom information.

        [Arguments]
            url[0] : string.
                Song ID to find.
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
        av_id = url[0] if len(url) else None
        request_type = params.get_string('type', REQUEST_LATEST)
        since = params.get_int('since', None)
        lang = params.get_string('lang', None)

        fields = None
        condition = []
        ordering_sql = None

        if av_id:  # Get one AV information
            limit = 0
            condition = ['id=%(id)s', {'id': av_id}]

        else:
            limit = params.get_limit('limit', 20)

            if request_type == REQUEST_POPLAR:  # Get popular AVs information
                ordering_sql = 'ORDER BY total_count DESC NULLS LAST, date DESC NULLS LAST'
            elif request_type == REQUEST_LATEST:  # Get latest AVs information
                now_date = datetime.utcnow().isoformat().split('T')[0]
                condition = ['date <= %(date)s', {'date': now_date}]
                ordering_sql = 'ORDER BY date DESC NULLS LAST'
            else:
                raise RequestError(ERR_REQUEST_ARG, str_data=('type.'))

        db_inst = PGClient(db='av')

        else_sql = '%s %s %s' % (
            ordering_sql if ordering_sql else '',
            'OFFSET %s' % since if since else '',
            'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
        )

        avs, rowcount = db_inst.query(
            table='video', fields=fields, condition=condition, ret_type='all', else_sql=else_sql
        )

        if not rowcount and av_id:
            raise RequestError(http_status=404)

        return Response(model_data={
            'metadata': avs,
            'detail': True if av_id else False
        })

    def add_count(self, url, params, request, response):
        """ Add user action count of choosen AV.

        [Arguments]
            url[0] : string.
                AV ID.
            type   : string.
                Action type.
        """
        # API args
        av_id = url[0] if len(url) else None
        action_type = params.get_string('type', None)

        if not action_type or action_type not in [USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY]:
            raise RequestError(ERR_REQUEST_ARG, str_data=('type error.'))

        db_inst = PGClient(db='av')

        cur, rowcount = db_inst.query(table='video', condition=['id=%(id)s', {'id': av_id}])
        if not rowcount:
            raise RequestError(ERR_DB_NOT_FOUND)
   
        count, total = self._add_user_action(action_type=action_type, av_id=av_id, db_inst=db_inst)

        db_inst.commit()

        return Response(content={
            'count': count,
            'total': total
        })

    def _add_user_action(self, action_type, av_id, db_inst):
        # record user action
        cur = db_inst.insert(table='video_statistics', data={
            'id': str(uuid4()),  # FIXME if we want use time uuid.
            'videoid': av_id,
            'type': action_type[0],
            'datetime': datetime.utcnow().isoformat()
        })

        # update count.
        sql = """
            UPDATE    video SET %(filed)s=%(filed)s+1, total_count=total_count+1
            WHERE     id='%(id)s' 
            RETURNING %(filed)s, total_count""" % {
            'filed': UA2field(action_type), 'id': av_id
        }
        cur = db_inst.execute(cmd=sql)

        return cur.fetchone()

    def get_metadata(self, url, params, request, response):
        """ Use AV id of any source to get all metadata.
        [Arguments]
            ids : list string.
                IDs of AVs to get metadata.
        """
        # API args
        ids = params.get_list('ids', None)
        if not ids:
            raise RequestError(ERR_REQUEST_ARG, str_data=('ids.'))

        resp = Response(content={'avs': {}})

        db_inst = PGClient(db='av')

        condition = ['id IN %(id)s', {'id': tuple(ids)}]
        avs, rowcount = db_inst.query(table='video', condition=condition, ret_type='all')

        for av in avs:
            resp['avs'][av['id']] = {'metadata': {}}

            resp['avs'][av['id']]['metadata'][DB_SRC_DMM] = {
                'id': av['id'],
                'source': DB_SRC_DMM,
                'title': av['title'],
                'posterurl': av['posterurl'],
                'duration': av['duration'],
                'stars': av['performer'],
                'genres': av['category'],
                'rating': av['rating'],
                'maker': av['maker'],
                'series': av['series'],
                'date': av['date'] and av['date'].strftime("%Y-%m-%d %H:%M:%S"),
                'description': av['description'],
                'samples': av['samples'],
                'url': av['url'],
                'date2': av['date2'] and av['date2'].strftime("%Y-%m-%d %H:%M:%S"),
                'code': av['code'],
                'md5sum': av['md5sum']
            }

        # patch up not found data.
        for missing_id in set(ids).difference(resp['avs'].keys()):
            resp['avs'][missing_id] = {}

        return resp
