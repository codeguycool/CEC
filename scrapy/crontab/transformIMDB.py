# std

import datetime
import ftplib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import traceback

from collections import defaultdict
from email.mime.text import MIMEText

# 3rd
import imdb
import lxml.html
import pycurl
import psycopg2
import requests

# settings
FTPHOST = 'ftp.fu-berlin.de'
FTPDIR = '/pub/misc/movies/database/'
LISTDIR = 'listdir'
CSVDIR = 'csvdir'
BACKUPDIR = 'backup'
SENDER = 'admin@admin'
RECEIVER = 'admin@admin'
DBNAME_CEC = 'CEC'
DBNAME_IMDB = 'IMDB'
URI = 'postgres://postgres@localhost/%s' % DBNAME_IMDB
POSTGRESQL_BIN_PATH = '/Library/PostgreSQL/9.4/bin/'
USR_LOCAL_BIN_PATH = '/usr/local/bin/'
USR_SBIN_PATH = '/usr/sbin/'


""" step1. download listfile
"""


def _getFileSize(url):
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(c.NOBODY, 1)
    c.perform()
    size = int(c.getinfo(c.CONTENT_LENGTH_DOWNLOAD))
    c.close()
    sys.stdout.flush()
    return size


def downloadListfile():
    print '\nstep1. download listfile\n'
    sys.stdout.flush()

    if not os.path.exists(LISTDIR):
        os.mkdir(LISTDIR)

    ftp = ftplib.FTP(host=FTPHOST)
    ftp.login()
    ftp.cwd(FTPDIR)

    for f in ftp.nlst():
        token = os.path.splitext(f)
        if token[1] == '.gz':
            maxtry = 10
            while True:
                try:
                    print('download ftp://%s%s%s' % (FTPHOST, FTPDIR, f))
                    url = 'ftp://%s%s%s' % (FTPHOST, FTPDIR, f)
                    destpath = '%s/%s' % (LISTDIR, f)

                    size1 = _getFileSize(url)
                    size2 = os.path.getsize(destpath) if os.path.exists(destpath) else 0
                    if size1 == size2:
                        break

                    destfile = open(destpath, 'wb')
                    c = pycurl.Curl()
                    c.setopt(pycurl.URL, url)
                    c.setopt(pycurl.WRITEDATA, destfile)
                    c.setopt(pycurl.NOPROGRESS, 0)
                    c.perform()
                    c.close()
                    sys.stdout.flush()
                    break
                except Exception as e:
                    maxtry -= 1
                    if maxtry >= 0:
                        print 'retry: %s, msg: %s' % (f, str(e))
                    else:
                        print 'download %s fail!' % f
                        raise

    print '\ndownload listfile is success!\n\n'


""" step2. import listfile to db
"""


def importListfile():

    print '\nstep2. import listfile to db\n'

    try:
        if os.path.exists(CSVDIR):
            shutil.rmtree(CSVDIR)
        os.mkdir(CSVDIR)
        # fixme imdbpy2sql csv need permisson, fix it if u can.
        os.chmod(CSVDIR, 0747)

        pwd = os.getcwd()
        # import csv need absolute path
        cmd = '%simdbpy2sql.py -d %s -u %s -c %s/%s -i table' % (USR_LOCAL_BIN_PATH, LISTDIR, URI, pwd, CSVDIR)
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print '\nerror occurred during import listfile to db, try to restore the older db\n'
        filepath = '%s/%s.bak' % (BACKUPDIR, DBNAME_CEC)
        _restoreDB(DBNAME_IMDB, filepath)
        print '\nrestore success!\n'
        raise

    print '\nimport listfile to db is success!\n\n'


""" step 3. import imdb db to table
"""


def _getMovie():
    # get movies if imdb_id is null
    conn = psycopg2.connect(database=DBNAME_IMDB, user='postgres')
    cursor = conn.cursor()
    cursor.execute('select id from title where imdb_id is null and kind_id = 1')
    return cursor.fetchall()


def _inserMovie(item):
    # insert into movies table
    conn = psycopg2.connect(database=DBNAME_CEC, user='postgres')
    cursor = conn.cursor()
    cursor.execute("""
    Insert into movies(id, source, title, akas, kind, genres, runtimes, rating, posterurl,
    directors, writers, stars, year, releaseDate, countries, languages, description, url, md5sum, udate)
    Values(%(id)s, %(source)s, %(title)s, %(akas)s, %(kind)s, %(genres)s, %(runtimes)s, %(rating)s, %(posterurl)s,
    %(directors)s, %(writers)s, %(stars)s, %(year)s, %(releaseDate)s, %(countries)s, %(languages)s, %(description)s,
    %(url)s, %(md5sum)s, %(udate)s)""", item)
    conn.commit()


def _updateMovie(movieid):
    # update imdbid = 0 if can't find imdbid
    conn = psycopg2.connect(database=DBNAME_IMDB, user='postgres')
    cursor = conn.cursor()
    cursor.execute("update title set imdb_id=0 where id=%s", (movieid,))
    conn.commit()


def _getRuntime(runtime):
    result = re.search(':*(\d+)(?:::)*', runtime)
    if result:
        return int(result.groups()[0])


def _getReleaseDt(releaseDt):
    result = re.search('(\w*):([^:]*)(?:::)*(.*)', releaseDt)
    if result:
        groups = result.groups()
        country = groups[0]
        dt = groups[1]
        memo = groups[2]
        return {'Default': dt, '%s%s' % (country, memo): dt}


def _isShortGenre(movie):
    if 'genres' in movie.data:
        for genre in movie.data['genres']:
            if genre == 'Short':
                return True
    return False


def _getPosterUrl(imdbid):
    url = 'http://www.omdbapi.com/?i=%s&plot=short&r=json' % imdbid
    r = requests.get(url)
    if r.ok:
        data = json.loads(r.text)
        if 'Poster' in data and data['Poster'] != 'N/A':
            return data['Poster']


def _getPosterUrl2(imdbid):
    url = 'http://www.imdb.com/title/%s/' % imdbid
    r = requests.get(url)
    if r.ok:
        element = lxml.html.fromstring(r.text)
        if len(element.xpath("//td[@id='img_primary']/div[@class='image']/a/img/@src")) == 1:
            return element.xpath("//td[@id='img_primary']/div[@class='image']/a/img/@src")[0]


def doTransform():

    print '\nstep3. import db to table\n'

    ia = imdb.IMDb(accessSystem='sql', uri=URI)
    while True:
        movies = _getMovie()
        if movies:
            for movieid in movies:
                try:
                    movie = ia.get_movie(movieid[0])

                    if _isShortGenre(movie):
                        _updateMovie(movieid[0])
                        continue

                    item = {}
                    item = defaultdict(lambda: None, item)

                    imdbid = 'tt%s' % ia.get_imdbID(movie)
                    if imdbid is not None:
                        item['source'] = imdb
                        item['id'] = 'im_' + imdbid
                        item['title'] = movie.data['title']

                        if 'akas' in movie.data:
                            item['akas'] = movie.data['akas']
                        else:
                            item['akas'] = []

                        if 'kind' in movie.data:
                            item['kind'] = movie.data['kind']

                        if 'genres' in movie.data:
                            item['genres'] = movie.data['genres']
                        else:
                            item['genres'] = []

                        if 'runtimes' in movie.data:
                            # fixme: if want to get all runtimes
                            item['runtimes'] = _getRuntime(movie.data['runtimes'][0])
                        if 'rating' in movie.data:
                            item['rating'] = movie.data['rating']

                        if 'director' in movie.data:
                            item['directors'] = [p.data['name'] for p in movie.data['director']]
                        else:
                            item['directors'] = []

                        if 'writer' in movie.data:
                            item['writers'] = [p.data['name'] for p in movie.data['writer']]
                        else:
                            item['writers'] = []

                        if 'cast' in movie.data:
                            item['stars'] = [p.data['name'] for p in movie.data['cast']]
                        else:
                            item['stars'] = []

                        if 'year' in movie.data:
                            item['year'] = movie.data['year']

                        if 'countries' in movie.data:
                            item['countries'] = movie.data['countries']
                        else:
                            item['countries'] = []

                        if 'languages' in movie.data:
                            item['languages'] = movie.data['languages']
                        else:
                            item['languages'] = []

                        if 'plot' in movie.data:
                            item['description'] = movie.data['plot'][0]

                        item['url'] = 'http://www.imdb.com/title/%s/' % imdbid
                        item['posterurl'] = _getPosterUrl(imdbid)
                        item['md5sum'] = hashlib.md5(json.dumps(item.__dict__, sort_keys=True)).hexdigest()
                        item['update'] = datetime.datetime.utcnow()
                        _inserMovie(item)
                    else:
                        _updateMovie(movieid[0])

                    print '%s is ok! imdbid:%s posterurl:%s' % (movieid[0], imdbid, item['posterurl'])
                except psycopg2.IntegrityError as e:
                    if e.pgcode == '23505':
                        sys.stdout.write(e.pgerror)
                except Exception:
                    print 'occurred exception on movie id: %s' % movieid
                    print traceback.format_exc()
        else:
            break

    print '\nimport db to table is success!\n'
    sys.stdout.flush()


""" step 4. backup db
"""


def backupDB():
    print '\nstep4. backup db\n'
    _backupDB(DBNAME_IMDB)
    _backupDB(DBNAME_CEC)
    print '\nbackup db is success!\n'


""" step5. test backup db file
"""


def testBackFile():
    print '\nstep5. test backup db file\n'
    sys.stdout.flush()
    _testBackupFile(DBNAME_IMDB)
    _testBackupFile(DBNAME_CEC)
    print '\ntest backupfile is success!\n'


def _testBackupFile(dbname):
    new_dbname = 'test_%s' % dbname
    backupfile = '%s.bak' % dbname
    print 'testing backup file:%s, try to restore db...\n' % backupfile
    sys.stdout.flush()
    _restoreDB(new_dbname, backupfile)
    _dropdb(new_dbname)


""" step6. move folder
"""


def moveBackupFile():
    print '\nstep6. move folder\n'
    _moveBackupFile(DBNAME_IMDB)
    _moveBackupFile(DBNAME_CEC)
    print 'move backup db file is success!\n\n'


def _moveBackupFile(dbname):
    newpath = '%s/%s.bak' % (BACKUPDIR, dbname)
    tmppath = '%s/%s.tmp' % (BACKUPDIR, dbname)

    # create backup directory
    if not os.path.exists(BACKUPDIR):
        os.mkdir(BACKUPDIR)

    # rename exist backup file
    if os.path.exists(newpath):
        # del tmp
        if os.path.exists(tmppath):
            os.remove(tmppath)
        # rename exist bak to tmp
        os.rename(newpath, tmppath)

    # move backup file to backup directory
    os.rename('%s.bak' % dbname, newpath)

    # del temp file
    if os.path.exists(tmppath):
        os.remove(tmppath)


""" sql function
"""


def _dropdb(dbname):
    cmd = "psql -U postgres -c 'drop database if exists \"%s\"'" % dbname
    subprocess.check_call(cmd, shell=True)


def _createdb(dbname):
    _dropdb(dbname)
    cmd = "createdb -U postgres %s" % dbname
    subprocess.check_call(cmd, shell=True)


def _backupDB(dbname):
    cmd = "pg_dump -U postgres -d %s -E utf-8 -f %s.bak" % (dbname, dbname)
    subprocess.check_call(cmd, shell=True)


def _restoreDB(dbname, filepath=None):
    # restore db
    if filepath is None:
        filepath = '%s.bak' % dbname

    _createdb(dbname)
    cmd = "psql -U postgres -d %s -f %s" % (dbname, filepath)
    subprocess.check_call(cmd, shell=True)


""" send notify message
"""


def sendMail(body, subject='Import IMDB interface fail!!!'):
    try:
        msg = MIMEText(body)
        msg["From"] = SENDER
        msg["To"] = RECEIVER
        msg["Subject"] = subject
        p = subprocess.Popen(["sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
        p.communicate(msg.as_string())
    except Exception:
        print traceback.format_exc()


if __name__ == '__main__':
    try:
        os.chdir(os.path.dirname(__file__))

        os.environ["PATH"] += os.pathsep + POSTGRESQL_BIN_PATH
        os.environ["PATH"] += os.pathsep + USR_LOCAL_BIN_PATH
        os.environ["PATH"] += os.pathsep + USR_SBIN_PATH

        st = datetime.datetime.now()
        # step1. download listfile
        downloadListfile()
        # # step2. import listfile to db
        # importListfile()
        # # step3. import db to table
        # doTransform()
        # # step4. backup db
        # backupDB()
        # # step5. test backup db file
        # testBackFile()
        # # step6. move backup db file
        # moveBackupFile()
        ed = datetime.datetime.now()

        message = 'Success!\n\nstart:%s\tend:%s' % (st, ed)
        sendMail(message, subject='Import success!')
        print message
    except Exception:
        print traceback.format_exc()
        sendMail(traceback.format_exc())