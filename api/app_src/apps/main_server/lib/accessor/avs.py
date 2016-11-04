""" Access tools for AVs.
"""

# std
from datetime import datetime

# app module
from app_var import MAX_RESPONSE_ROWS
from framework.common_tools import escape_wildcard
from framework.db_client.pg_client import PGClient


def search_avs(keyword, file_filter, keyword_filter, ordering=0, since=None, limit=10, lang=None):
    """ Search AVs information.

    [Arguments]
        keyword : list.
            Search keyword.
        file_filter   : int. (Not implement)
            File filter.
        keyword_filter  : list.
            Keyword filter.
        ordering  : int.
            Ordering rule.
        since  : int.
            Response data start from.
        limit  : int.
            Number of response rows to display.
        lang  : string.
            To choose display content.
    """
    keyword = list(set(keyword))
    keyword_filter = list(set(keyword_filter))

    db_inst = PGClient(db='av')

    # Compose SQL
    keyword_sql = u' OR '.join(
        [u"keywords ILIKE '%{0}%'".format(escape_wildcard(k)) for k in keyword])

    if keyword_filter:
        keyword_filter_sql = u' OR '.join(
            [u"keywords ILIKE '%{0}%'".format(escape_wildcard(k)) for k in keyword_filter])
        condition_sql = '(%s) AND (%s)' % (keyword_sql, keyword_filter_sql)
    else:
        condition_sql = keyword_sql

    if ordering == 1:
        ordering_sql = u"ORDER BY date ASC NULLS LAST"
    elif ordering == 2:
        ordering_sql = u"ORDER BY total_count DESC NULLS LAST, date DESC NULLS LAST"
    elif ordering == 3:
        ordering_sql = u"ORDER BY total_count ASC NULLS LAST, date ASC"
    else:
        ordering_sql = u"ORDER BY date DESC NULLS LAST"

    sql = u'''
        SELECT *
        FROM   video
        WHERE  id IN (
                    SELECT id
                    FROM   video_keyword
                    WHERE  {0}
               )
               AND date <= '{4}'
        {1} {2} {3}
    '''.format(
        condition_sql,
        ordering_sql,
        u'OFFSET %s' % since if since else '',
        u'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS,
        datetime.utcnow().isoformat().split('T')[0]
    )
    videos = db_inst.execute(cmd=sql).fetchall()

    return {
        'metadata': videos
    }


def search_total(keyword, lang=None, db_inst=None):
    keyword = list(set(keyword))

    if not db_inst:
        db_inst = PGClient(db='av')

    # Compose SQL
    keyword_sql = u' OR '.join(
        [u"keywords ILIKE '%{0}%'".format(escape_wildcard(k)) for k in keyword])

    sql = u'''
        SELECT COUNT(*)
        FROM   video, video_keyword
        WHERE  ({0}) AND video.id=video_keyword.id AND video.date <= '{1}'
    '''.format(
        keyword_sql,
        datetime.utcnow().isoformat().split('T')[0]
    )
    return db_inst.execute(cmd=sql).fetchone()[0]


def suggest_keyword(media_id, lang, db_inst=None):
    if not db_inst:
        db_inst = PGClient(db='av')

    condition = ['id=%(id)s', {'id': media_id}]
    rows, rowcount = db_inst.query(table='video', fields=['title, code'], condition=condition, ret_type='all')

    return rows.pop() if rowcount else []
