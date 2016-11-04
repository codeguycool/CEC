""" Access tools for karaokes.
"""

# std
from collections import defaultdict

# app module
from app_var import MAX_RESPONSE_ROWS
from framework.common_tools import escape_wildcard
from framework.db_client.pg_client import PGClient


def search_karaokes(keyword, file_filter, keyword_filter, ordering=0, since=None, limit=10, lang=None):
    """ Search karaokes information.

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

    db_inst = PGClient(db='karaoke')

    # Compose SQL
    keyword_sql = u' OR '.join(
        [u"songs.title ILIKE '%{0}%' OR songs.artist ILIKE '%{0}%'".format(escape_wildcard(k)) for k in keyword])

    if keyword_filter:
        keyword_filter_sql = u' OR '.join(
            [u"songs.title ILIKE '%{0}%' OR songs.artist ILIKE '%{0}%'".format(escape_wildcard(k)) for k in keyword_filter]
        )
        condition_sql = '(%s) AND (%s)' % (keyword_sql, keyword_filter_sql)
    else:
        condition_sql = keyword_sql

    if ordering == 1:
        ordering_sql = u"ORDER BY title"  # TODO
    elif ordering == 2:
        ordering_sql = u"ORDER BY total_count DESC NULLS LAST, title"
    elif ordering == 3:
        ordering_sql = u"ORDER BY total_count ASC NULLS LAST, title"
    else:
        ordering_sql = u"ORDER BY title"  # TODO

    # Note here duplicate field overlaped.
    sql = u'''
        SELECT songs.*, song_content.*
        FROM   songs, song_content
        WHERE  songs.keymd5=song_content.keymd5 AND ({0})
        {1} {2} {3}
    '''.format(
        condition_sql,
        ordering_sql,
        u'OFFSET %s' % since if since else '',
        u'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
    )
    songs = db_inst.execute(cmd=sql).fetchall()

    return {
        'metadata': songs
    }


def get_karaokes_content(karaokes_row, db_inst=None):
    """ Get karaokes content by karaoke id from given row data.
    [Arguments]
        karaokes_row : list.
            Movie rows data.
        db_inst    : DB client instance.
            Set for reuse client.

    [Return]
        content: dict
            Karaoke content row data with key is karaoke id.
    """
    if not db_inst:
        db_inst = PGClient()

    id_sqls = []
    for row in karaokes_row:
        value = row.get('keymd5', None)
        if value:
            id_sqls.append("keymd5='%s'" % value)

    if not id_sqls:
        return {}

    cond_sql = "source='youtube' AND (%s)" % ' OR '.join(id_sqls)  # FIXME: If movie has other source.
    content, rowcount = db_inst.query(table='song_content', condition=[cond_sql], ret_type='all')

    ret = defaultdict(list)
    for row in content:
        ret[row['keymd5']].append(row)  # FIXME: It may need sorting.

    return ret


def search_total(keyword, lang=None, db_inst=None):
    keyword = list(set(keyword))

    if not db_inst:
        db_inst = PGClient(db='karaoke')

    # Compose SQL
    keyword_sql = u' OR '.join(
        [u"songs.title ILIKE '%{0}%' OR songs.artist ILIKE '%{0}%'".format(escape_wildcard(k)) for k in keyword])

    sql = u'''
        SELECT COUNT(*)
        FROM   songs, song_content
        WHERE  songs.keymd5=song_content.keymd5 AND ({0})
    '''.format(
        keyword_sql
    )
    return db_inst.execute(cmd=sql).fetchone()[0]
