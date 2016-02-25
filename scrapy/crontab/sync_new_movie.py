# -*- coding: utf-8 -*-

""" 同步資料到雲端上的Database

    install
    =======
    sudo pip install requests
    sudo pip install psycopg2

"""

# std lib
import datetime
import hashlib
import json
import logging
import os
import time
import traceback

# 3rd lib
import psycopg2
import requests

# tmp目錄的path, 如果使用os.getcwd()會建立在呼叫程式的目錄下, 所以要利用程式本身的位置來建立
TEMP_PATH = os.path.normpath('%s/tmp' % os.path.dirname(os.path.realpath(__file__)))

# 建立tmp目錄
if not os.path.exists(TEMP_PATH):
    os.mkdir(TEMP_PATH)
os.chmod(TEMP_PATH, 0747)

DB_NAME = 'qmdb'
DB_HOST = 'localhost'
CLOUD_IP = '192.168.73.222'
CLOUD_PORT = '80'


def is_task_done(task):
    """ 查看某個task是否完成

    :param task:
    :return:
    """
    response = requests.get('http://%s:%s/dbsync/task_status?task=%s' % (CLOUD_IP, CLOUD_PORT, task))
    try:
        json_result = json.loads(response.content)
        flag = json_result.get('task_done', False)
        return flag
    except:
        return None


def _get_movie_source():
    """ 取得所有的 movies 資料來源的代碼

    :return:
    """
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user='postgres')
        cursor = conn.cursor()
        cursor.execute('select distinct source from movies;')
        return cursor.fetchall()
    except:
        logging.error(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()


def _get_new_release_movies(source):
    """ 利用 bttt(bt天堂) 的資料，取出有對應到的 movies

    :param source: movies 資料來源代碼, 'imdb'/'douban'/'atmovies'...
    :return:
    """
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user='postgres')
        cursor = conn.cursor()
        cursor.execute("""
        select m.imdbid from movies m
        left join bttt b
        on m.imdbid = b.imdbid
        where b.id is not null
        and m.imdbid is not null
        and m.title != ''
        and m.posterurl is not null
        and m.directors != '{}'
        and m.writers != '{}'
        and m.stars != '{}'
        and m.description is not null
        and m.source = '%s'
        and m.source != 'chinayes'
        order by b.udate desc
        limit 22
        """ % (source,))
        return cursor.fetchall()
    except:
        logging.error(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()


def sync_new_movies():
    """ Call cloud api(http://{CLOUD_IP}:{CLOUD_PORT}/dbsync/update_latest_movies) to sync new movies

    :return:
    """
    # query new movies
    new_movies = set()
    source_list = _get_movie_source()
    for source in source_list:
        movies = _get_new_release_movies(source[0])
        for movie in movies:
            new_movies.add(movie[0])
    # call cloud api
    form_data = {'imdbid_list': str(list(new_movies))}
    response = requests.put('http://%s:%s/dbsync/update_latest_movies' % (CLOUD_IP, CLOUD_PORT), data=form_data)
    try:
        json_result = json.loads(response.content)
        rowcount = dict.get(json_result, 'rowcount', 0)
        if rowcount != len(new_movies):
            logging.info(json_result)
        else:
            logging.info('update latest movies success!')
    except:
        logging.error(traceback.format_exc())


def _save_patch_data(dbname, fields_fmt, filepath,  timestamp):
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user='postgres')
    cursor = conn.cursor()
    if os.path.exists(filepath):
        os.remove(filepath)
    cursor.execute("""copy (select %s from %s where udate > '%s' order by udate) to '%s'""" % (fields_fmt, dbname, timestamp, filepath))


def _get_timestamp(resource):
    """ 取得某個resource(table)的最後更新的日期(timestamp)

    :param resource: table name
    :return:
    """
    response = requests.get('http://%s:%s/dbsync/last_timestamp?entity=%s' % (CLOUD_IP, CLOUD_PORT, resource))
    json_result = json.loads(response.content)
    timestamp = json_result['timestamp']
    if timestamp is None:
        timestamp = datetime.datetime.min
    return timestamp


def _getmd5(filepath):
    """ 計算md5

    :param filepath:
    :return:
    """
    hash = hashlib.md5()
    with open(filepath, mode='rb') as fp:
        for chunk in iter(lambda: fp.read(4096), ""):
            hash.update(chunk)
    return hash.hexdigest()


def _rename2md5(filepath):
    """ 將檔案重新以檔案的MD5命名

    :param filepath:
    :return:
    """
    md5sum = _getmd5(filepath)
    md5sum_filepath = '%s/%s' % (TEMP_PATH, md5sum)
    os.rename(filepath, md5sum_filepath)
    return md5sum_filepath


def _patch_db(dbname, fields_fmt='*'):
    """ 上傳DB的主要程式

    :param dbname:
    :param fields_fmt:
    :return:
    """
    filepath = '%s/%s.csv' % (TEMP_PATH, dbname)
    md5_filepath = None
    try:
        _save_patch_data(dbname, fields_fmt, filepath,  _get_timestamp(dbname))
        md5_filepath = _rename2md5(filepath)
        # if os.path.getsize(md5_filepath) == 0:
        #     raise Exception('file is empty')
        files = {
            'patchfile': open(md5_filepath, mode='rb')
        }
        response = requests.post('http://%s:%s/dbsync/patch_%s' % (CLOUD_IP, CLOUD_PORT, dbname), files=files, stream=True)
        json_result = json.loads(response.content)
        logging.debug(json_result)
    except:
        logging.error(traceback.format_exc())
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(md5_filepath):
            os.remove(md5_filepath)


def patch_movies():
    """ 上傳movies

    :return:
    """
    fields = ('id', 'source', 'title', 'akas', 'kind', 'genres', 'u_genres', 'runtimes', 'rating', 'posterurl',
              'directors', 'writers', 'stars', 'year', 'releasedate', 'countries', 'u_countries', 'languages',
              'u_languages', 'description', 'imdbid', 'url', 'vcount', 'dcount', 'pcount', 'total_count',
              'udate', 'md5sum')
    _patch_db('movies', '%s' % ','.join(fields))


def patch_movie_content():
    """ 上傳movie_content

    :return:
    """
    fields = ('id', 'source', 'title', 'akas', 'year', 'imdbid', 'info_url', 'content_url', 'udate', 'md5sum')
    _patch_db('movie_content', '%s' % ','.join(fields))


def rebuild_movie_keyword():
    """ 呼叫 cloud上 的API，重建movie_keyword table

    :return:
    """
    response = requests.put('http://%s:%s/dbsync/rebuild_movie_keyword' % (CLOUD_IP, CLOUD_PORT))
    json_result = json.loads(response.content)
    logging.info(json_result)


def _check_status(task):
    # check status
    expire = datetime.datetime.now() + datetime.timedelta(minutes=10)
    while True:
        flag = is_task_done(task)
        if flag is None:
            return False
        if flag:
            return True
        time.sleep(30)

        if datetime.datetime.now() > expire:
            logging.error("'%s' task expired" % task)
            return False


def sync():
    """ daily sync task

    :return:
    """
    # 1. movies
    patch_movies()
    flag = _check_status('patch_movies')
    if flag is False:
        return

    # 2. movie_content
    patch_movie_content()
    flag = _check_status('patch_movie_content')
    if flag is False:
        return

    # 3. movie_keyword
    rebuild_movie_keyword()
    flag = _check_status('rebuild_movie_keyword')
    if flag is False:
        return

    # 4. movie_latest
    sync_new_movies()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    st = datetime.datetime.now()
    sync()
    ed = datetime.datetime.now()
    logging.debug(ed - st)