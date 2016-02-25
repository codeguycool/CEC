# std
import os
import time

# project
from CEC.settings import DIR_CACHE


def savecache(name, vid, rawtxt, force=False):
    cache_spider_dir = '%s/%s' % (DIR_CACHE, name)
    if not os.path.exists(DIR_CACHE):
        os.mkdir(DIR_CACHE)
    if not os.path.exists(cache_spider_dir):
        os.mkdir(cache_spider_dir)

    write_mode = 'w+' if force else 'w'
    with open('%s/%s.html' % (cache_spider_dir, vid), mode=write_mode) as f:
        f.writelines(rawtxt)


def is_page_exist(name, vid):
    page_path = '%s/%s/%s.html' % (DIR_CACHE, name, vid)
    return True if os.path.exists(page_path) else False


def is_page_expire(name, vid, day=30):
    page_path = '%s/%s/%s.html' % (DIR_CACHE, name, vid)
    now = time.time()
    timestamp = now - 60 * 60 * 24 * day
    return True if timestamp > os.path.getctime(page_path) else False


def get_body(name, vid):
    page_path = '%s/%s/%s.html' % (DIR_CACHE, name, vid)
    body = None
    with open(page_path, mode='r') as f:
        body = f.read()

    return body

if __name__ == '__main__':
    pass