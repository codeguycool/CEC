""" Access tools for movies.
"""

# std
from collections import defaultdict

# app module
from app_var import MAX_RESPONSE_ROWS
from framework.db_client.pg_client import PGClient
from framework.sys_const import (
    LANG_TCH, LANG_SCH, LANG_ENG,
    DB_SRC_ATMOVIES, DB_SRC_DOUBAN, DB_SRC_IMDB,
    DB_ID_PRE_ATMOVIES, DB_ID_PRE_DOUBAN, DB_ID_PRE_IMDB
)


def search_movies(keyword, file_filter, keyword_filter, ordering=0, since=None, limit=10, lang=None):
    """ Search movies information.

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

    db_inst = PGClient()

    # Compose SQL
    sql_data = {}

    keyword_sql = _gen_keyword_sql(keyword, sql_data)

    if keyword_filter:
        keyword_filter_sql = _gen_keyword_sql(keyword_filter, sql_data, prefix_key='kf')
        condition_sql = u'(%s) && (%s)' % (keyword_sql, keyword_filter_sql)
    else:
        condition_sql = keyword_sql

    if ordering == 1:
        ordering_sql = u"ORDER BY releasedate->>'Default' ASC NULLS LAST"
    elif ordering == 2:
        ordering_sql = u"ORDER BY total_count DESC NULLS LAST, releasedate->>'Default' DESC NULLS LAST"
    elif ordering == 3:
        ordering_sql = u"ORDER BY total_count ASC NULLS LAST, releasedate->>'Default' ASC"
    else:
        ordering_sql = u"ORDER BY releasedate->>'Default' DESC NULLS LAST"

    sql = u'''
        SELECT *
        FROM   movies
        WHERE  id IN (
            SELECT id
            FROM   movie_keyword
            WHERE  source = '{1}' AND ({0}) @@ j_tsv
        )
        {2} {3} {4}
    '''.format(
        condition_sql,
        lang2source(lang),
        ordering_sql,
        u'OFFSET %s' % since if since else '',
        u'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
    )
    movies = db_inst.execute(cmd=sql, data=sql_data).fetchall()

    content = get_movies_content(movies_row=movies, db_inst=db_inst)

    return {
        'metadata': movies,
        'content': content
    }


def _gen_keyword_sql(keyword, sql_data, prefix_key='k'):
    """ Generate tsquery sql of keyword.
    [Arguments]
        keyword  : list.
            A list of query keywords.
        sql_data : dict.
            A dict of sql data.
        prefix_key:
            Prefix string of data key.

    [Return]
        sub_sql: string
    """
    sub_sqls = []
    
    for i, k in enumerate(keyword):
        key = '%s%s' % (prefix_key, i)
        sub_sqls.append(u"plainto_tsquery('jiebacfg', %({0})s)".format(key))
        sql_data[key] = k
    return u' || '.join(sub_sqls)


def get_movies_content(movies_row, db_inst=None):
    """ Get movies content by imdb id from given row data.
    [Arguments]
        movies_row : list.
            Movie rows data.
        db_inst    : DB client instance.
            Set for reuse client.

    [Return]
        content: dict
            Movie content row data with key is imdb id.
    """
    if not db_inst:
        db_inst = PGClient()

    id_sqls = []
    for row in movies_row:
        imdb_id = row.get('imdbid', None)
        if imdb_id:
            id_sqls.append("imdbid='%s'" % imdb_id)

    if not id_sqls:
        return {}

    cond_sql = "source='tudou' AND (%s)" % ' OR '.join(id_sqls)  # FIXME: If movie has other source.
    content, rowcount = db_inst.query(table='movie_content', condition=[cond_sql], ret_type='all')

    ret = defaultdict(list)
    for row in content:
        ret[row['imdbid']].append(row)  # FIXME: It may need sorting.

    return ret


def search_total(keyword, lang=None, db_inst=None):
    keyword = list(set(keyword))

    if not db_inst:
        db_inst = PGClient()

    # Compose SQL
    sql_data = {}
    keyword_sql = _gen_keyword_sql(keyword, sql_data)

    sql = u'''
        SELECT COUNT(*)
        FROM   movies
        WHERE  id IN (
            SELECT id
            FROM   movie_keyword
            WHERE  source = '{1}' AND ({0}) @@ j_tsv
        )
    '''.format(
        keyword_sql,
        lang2source(lang)
    )
    return db_inst.execute(cmd=sql, data=sql_data).fetchone()[0]


def lang2source(lang):
    """ Mapping language type to movie source.
    """
    return {
        LANG_ENG: DB_SRC_IMDB,
        LANG_SCH: DB_SRC_DOUBAN,
        LANG_TCH: DB_SRC_ATMOVIES
    }.get(lang, DB_SRC_IMDB)


def lang2id_pre(lang):
    """ Mapping language type to movie id prefix.

    [Arguments]
        lang : string.
            Value of UI language.
    """
    return {
        LANG_ENG: DB_ID_PRE_IMDB,
        LANG_SCH: DB_ID_PRE_DOUBAN,
        LANG_TCH: DB_ID_PRE_ATMOVIES
    }.get(lang, DB_ID_PRE_IMDB)


def source2lang(source):
    """ Mapping movie source to language type.
    """
    return {
        DB_SRC_IMDB: LANG_ENG,
        DB_SRC_DOUBAN: LANG_SCH,
        DB_SRC_ATMOVIES: LANG_TCH
    }.get(source, None)


def suggest_keyword(media_id, lang, db_inst=None):
    if not db_inst:
        db_inst = PGClient()

    # Get target movies info
    condition = ['id=%(id)s', {'id': media_id}]
    rows, rowcount = db_inst.query(
        table='movies', fields=['source, title, imdbid'], condition=condition, ret_type='all'
    )

    if not rowcount:
        return []
    
    if rows[0]['imdbid']:  # if it has imdbid, then here attempt to get other source data.
        condition = ['imdbid=%(imdbid)s AND id!=%(id)s', {'imdbid': rows[0]['imdbid'], 'id': media_id}]
        other_rows, rowcount = db_inst.query(
            table='movies', fields=['source, title'], condition=condition, ret_type='all'
        )
        rows.extend(other_rows)

    # Filter data by lang rules.
    filter_list = {
        LANG_ENG: [DB_SRC_IMDB],
        LANG_SCH: [DB_SRC_IMDB, DB_SRC_DOUBAN],
        LANG_TCH: [DB_SRC_IMDB, DB_SRC_DOUBAN, DB_SRC_ATMOVIES]
    }[lang]

    return [row['title'] for row in rows if row['source'] in filter_list]
