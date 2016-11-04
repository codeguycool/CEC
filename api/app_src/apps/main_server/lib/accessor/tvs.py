""" Access tools for dramas.
"""
# app module
from app_var import MAX_RESPONSE_ROWS
from framework.common_tools import escape_wildcard
from framework.db_client.pg_client import PGClient
from framework.sys_const import (
    LANG_ENG, LANG_SCH, LANG_TCH,
    DB_SRC_IMDB, DB_SRC_DOUBAN, DB_SRC_ATMOVIES, DB_SRC_KUBO,
    DB_ID_PRE_IMDB, DB_ID_PRE_DOUBAN, DB_ID_PRE_ATMOVIES, DB_ID_PRE_KUBO
)


def search_tvs(keyword, file_filter, keyword_filter, ordering=0, since=None, limit=10, lang=None):
    """ Search dramas information.

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
    db_inst = PGClient()

    # Compose SQL
    if ordering == 1:
        ordering_sql = u"ORDER BY rdate ASC NULLS LAST"
    elif ordering == 2:
        ordering_sql = u"ORDER BY total_count DESC NULLS LAST, rdate DESC NULLS LAST"
    elif ordering == 3:
        ordering_sql = u"ORDER BY total_count ASC NULLS LAST, rdate ASC"
    else:
        ordering_sql = u"ORDER BY rdate DESC NULLS LAST"

    sql = u'''
            {0}
            {1} {2} {3}
        '''.format(
        get_search_sql_without_order(lang, keyword, keyword_filter),
        ordering_sql if ordering_sql else '',
        'OFFSET %s' % since if since else '',
        'LIMIT %s' % limit if MAX_RESPONSE_ROWS > limit > 0 else 'LIMIT %s' % MAX_RESPONSE_ROWS
    )

    dramas = db_inst.execute(cmd=gen_fetch_dramas_sql(dramas_sql=sql)).fetchall()

    return {
        'metadata': dramas
    }


def gen_fetch_dramas_sql(dramas_sql):
    """ To wrap column data.

    [Arguments]
        dramas_sql : string.
            A complete sql to get dramas row which is sorted and limited.
    """
    # TODO: play_link can remove, if SPEC has not play icon any more.
    return u'''
        SELECT id, source, title, akas, kind, genres, posterurl, stars, year, region, description, url,
               ARRAY(SELECT json_object_keys(play_urls)) AS file_source, update_eps, total_eps, completed,
               rdate, NULL AS play_link
        FROM   ({0}) AS data 
    '''.format(dramas_sql)


def search_total(keyword, lang=None, db_inst=None):
    """ Search dramas count.

    [Arguments]
        keyword : list.
            Search keyword.
        lang  : string.
            To choose display content.
    """
    if not db_inst:
        db_inst = PGClient()

    # Compose SQL
    sql = u'''
        select count(*) from (
        {0}
        ) as data
    '''.format(
        get_search_sql_without_order(lang, keyword, None)
    )
    return db_inst.execute(cmd=sql).fetchone()[0]


def get_search_sql_without_order(lang, keyword, keyword_filter):

    if keyword_filter:
        condition_sql = get_condition_sql_with_filter(keyword, keyword_filter)
    else:
        condition_sql = get_condition_sql_without_filter(keyword)

    sql = u'''
    select * from drama where id in (
        select id from drama_keyword where source = '{0}' and {1}
    )
    '''.format(
        lang2source(lang),
        condition_sql
    )
    return sql


def compose_ilike_sql_by_keywords(keywords):
    unique_keywords = list(set(keywords))
    condition_sql = u' OR '.join(
        [u"keywords ILIKE '%{0}%'".format(escape_wildcard(k)) for k in unique_keywords])
    return condition_sql


def get_condition_sql_without_filter(keyword):
    return compose_ilike_sql_by_keywords(keyword)


def get_condition_sql_with_filter(keyword, keyword_filter):
    condition_sql = '(%s) AND (%s)' % (
        compose_ilike_sql_by_keywords(keyword), compose_ilike_sql_by_keywords(keyword_filter)
    )
    return condition_sql


def lang2source(lang):
    """ Mapping language type to source.
    """
    return {
        LANG_ENG: DB_SRC_IMDB,
        LANG_SCH: DB_SRC_DOUBAN,
        LANG_TCH: DB_SRC_KUBO
    }.get(lang, DB_SRC_IMDB)
