"""Model class
"""

# std
from datetime import datetime
from uuid import uuid4

# app module
from app_var import MAX_RESPONSE_ROWS
from accessor.karaokes import get_karaokes_content
from api.const import USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY
from api.tools import UA2field
from framework.db_client.pg_client import PGClient
from framework.err import ERR_DB_NOT_FOUND, ERR_REQUEST_ARG, RequestError
from framework.response import Response
from framework.sys_const import LANG_TCH


ARG_SONG_LANGS = ['M', 'E', 'T', 'C', 'J']


class KaraokesModel:

    def get_karaokes(self, url, params, request, response):
        """ Get karaokes information.

        [API]
            1) GET RESOURCE/${KARAOKE_ID}
                Get target karaokes detail information.

            2) GET RESOURCE?type=${TYPE}
                Get custom information.

        [Arguments]
            url[0] : string.
                Song ID to find.
            since  : int string.
                Response data start from.
            limit  : int string.
                Number of response rows to display.
            lang  : string.
                To choose display content.
            song_lang  : string.
                To choose language type of songs.
            list_type  : int string.
                To choose songs list type.
        """
        # API args
        karaoke_id = url[0] if len(url) else None
        since = params.get_int('since', None)
        lang = params.get_string('lang', None)

        table = 'songs'
        fields = None
        condition = []
        ordering_sql = None

        if karaoke_id:  # Get one song information
            limit = 0
            condition = ['keymd5=%(id)s', {'id': karaoke_id}]

        else:  # Get song list information
            limit = params.get_limit('limit', 20)

            song_lang = params.get_string('song_lang', 'M')
            if song_lang not in ARG_SONG_LANGS:
                raise RequestError(ERR_REQUEST_ARG, str_data=('song_lang.'))

            list_type = params.get_int('list_type', 1)
            if list_type not in xrange(1, 4):
                raise RequestError(ERR_REQUEST_ARG, str_data=('list_type.'))

            table = 'songs, song_list'
            fields = ['songs.*', 'song_list.udate AS list_udate']
            condition = [
                'songs.keymd5=song_list.keymd5 AND (song_list.lang=%(lang)s AND song_list.type=%(type)s)',
                {'lang': song_lang, 'type': str(list_type)}
            ]
            ordering_sql = 'ORDER BY song_list.rank'

        db_inst = PGClient(db='karaoke')

        else_sql = '%s %s %s' % (
            ordering_sql if ordering_sql else '',
            'OFFSET %s' % since if since else '',
            'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
        )

        songs, rowcount = db_inst.query(
            table=table, fields=fields, condition=condition, ret_type='all', else_sql=else_sql
        )

        if not rowcount and karaoke_id:
            raise RequestError(http_status=404)

        content = get_karaokes_content(karaokes_row=songs, db_inst=db_inst)

        return Response(model_data={
            'metadata': songs,
            'content': content,
            'detail': True if karaoke_id else False
        })

    def add_count(self, url, params, request, response):
        """ Add user action count of choosen karaoke.

        [Arguments]
            url[0] : string.
                Karaoke ID.
            type   : string.
                Action type.
        """
        # API args
        karaoke_id = url[0] if len(url) else None
        id_list = params.get_list('ids', [])
        action_type = params.get_string('type', None)

        if not action_type or action_type not in [USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY]:
            raise RequestError(ERR_REQUEST_ARG, str_data=('type error.'))

        if karaoke_id:
            id_list = [karaoke_id]
        elif not id_list:
            raise RequestError(ERR_REQUEST_ARG, str_data=('id_list error.'))

        db_inst = PGClient(db='karaoke')

        cur, rowcount = db_inst.query(table='songs', condition=['keymd5 IN %(ids)s', {'ids': tuple(id_list)}])
        if rowcount != len(id_list):
            raise RequestError(ERR_DB_NOT_FOUND)
   
        resp = Response()

        for ID in id_list:
            count, total = self._add_user_action(action_type=action_type, karaoke_id=ID, db_inst=db_inst)
            resp[ID] = {
                'count': count,
                'total': total
            }

        db_inst.commit()

        return resp.pop(karaoke_id) if karaoke_id else resp

    def _add_user_action(self, action_type, karaoke_id, db_inst):
        # record user action
        cur = db_inst.insert(table='song_statistics', data={
            'id': str(uuid4()),  # FIXME if we want use time uuid.
            'keymd5': karaoke_id,
            'type': action_type[0],
            'datetime': datetime.utcnow().isoformat()
        })

        # update count.
        sql = """
            UPDATE    songs SET %(filed)s=%(filed)s+1, total_count=total_count+1
            WHERE     keymd5='%(id)s' 
            RETURNING %(filed)s, total_count""" % {
            'filed': UA2field(action_type), 'id': karaoke_id
        }
        cur = db_inst.execute(cmd=sql)

        return cur.fetchone()

    def get_covers(self, url, params, request, response):
        """ Get karaoke covers.

        [Arguments]
            song_langs : list string.
                Karaoke ID.
            list_type  : int string.

        """
        song_langs = params.get_list('song_langs', [])
        song_langs = [v for v in song_langs if v in ARG_SONG_LANGS]
        if not song_langs:
            raise RequestError(ERR_REQUEST_ARG, str_data=('song_langs.'))

        list_type = params.get_int('list_type', 1)
        if list_type not in xrange(1, 4):
            raise RequestError(ERR_REQUEST_ARG, str_data=('list_type.'))

        # Take the cover of first row of each song lang as index cover.
        table = u'''
            song_content, 
            (
                SELECT   DISTINCT ON (lang)
                         keymd5, lang
                FROM     song_list
                WHERE    lang IN %(lang)s AND type=%(type)s
                ORDER BY lang, rank
            ) l
        '''
        fields = ['song_content.poster_url', 'l.lang']
        condition = [u'song_content.keymd5=l.keymd5', {'lang': tuple(song_langs), 'type': str(list_type)}]

        db_inst = PGClient(db='karaoke')

        rows, rowcount = db_inst.query(table=table, fields=fields, condition=condition, ret_type='all')
        covers = {row['lang']: row['poster_url'] for row in rows}

        return Response(content={
            'covers': {key: covers[key] if covers.has_key(key) else None for key in song_langs}
        })

    def get_metadata(self, url, params, request, response):
        """ Use karaokes id of any source to get all metadata.
        [Arguments]
            ids : list string.
                IDs of karaokes to get metadata.
        """
        # API args
        ids = params.get_list('ids', None)
        if not ids:
            raise RequestError(ERR_REQUEST_ARG, str_data=('ids.'))

        resp = Response(content={'karaokes': {}})

        db_inst = PGClient(db='karaoke')

        condition = ['keymd5 IN %(id)s', {'id': tuple(ids)}]
        karaokes, rowcount = db_inst.query(table='songs', condition=condition, ret_type='all')

        for karaoke in karaokes:
            resp['karaokes'][karaoke['keymd5']] = {'metadata': {}}

            # Get content data.
            condition = ['keymd5 = %(id)s', {'id': karaoke['keymd5']}]
            rows, rowcount = db_inst.query(table='song_content', condition=condition, ret_type='all')
            content = rows[0] if rows else {}

            # Key name use lang instead of source name and we only have TCH data,
            # because TCH dad is composed of cashbox, holiday and youtube.
            resp['karaokes'][karaoke['keymd5']]['metadata'][LANG_TCH] = {
                'id': karaoke['keymd5'],
                'source': karaoke['source'],
                'title': karaoke['title'],
                'artist': karaoke['artist'],
                'song_lang': karaoke['lang'],
                # use content
                'posterurl': content['poster_url'],
                'description': content['description'],
                'play_url': content['play_url'],
                'md5sum': content['md5sum']
            }

        # patch up not found data.
        for missing_id in set(ids).difference(resp['karaokes'].keys()):
            resp['karaokes'][missing_id] = {}

        return resp

