# -*-coding: utf-8 -*-

""" data patcher factory

set patcher variables(sqlcmd, db....)

"""

# std
import datetime

# proj
from framework.db_client.pg_client import PGClient
from framework.sys_tools import g
from patch_data_task import PatchDataTask


def create_patcher(tablename):
    """ factory method

    :param tablename:
    :return:
    """
    patchers = {
        'movies': MoviesPatcher,
        'movie_content': MovieContentPatcher,
        'songs': SongsPatcher,
        'song_content': SongcontentPatcher,
        'song_list': SonglistPatcher,
        'video': AvVideoPatcher,
        'drama': DramaPatcher
    }
    patch = patchers.get(tablename, None)
    return patch() if patch else None


class BasePatcher(object):

    def __init__(self, db):
        if db is None:
            raise ValueError('db is None')
        self.db = db
        self.tablename = self._set_tablename()
        self.temp_table_sqlcmd = self._set_temp_table_sqlcmd()
        self.sqlcmd = self._set_sqlcmd()
        self.temp_table_name = self._set_tmptablename()

    def get_db(self):
        return self.db

    def _set_tablename(self):
        raise NotImplementedError

    def get_tablename(self):
        return self.tablename

    def _set_temp_table_sqlcmd(self):
        raise NotImplementedError

    def _set_sqlcmd(self):
        raise NotImplementedError

    def _set_tmptablename(self):
        return 'temp_%s' % self.tablename

    def get_columns(self):
        raise NotImplementedError

    def patch(self, fileobj, taskname):
        bg_task = PatchDataTask(fileobj, self)
        g().set(taskname, bg_task)
        bg_task.start()

    def get_timestamp(self):
        db_inst = PGClient(self.db, timeout=False)
        cur = db_inst.execute('select max(udate) from %s' % (self.tablename,))
        timestamp = cur.fetchone()[0]
        if timestamp is None:
            timestamp = datetime.datetime.min
        return timestamp


class QmdbPatcher(BasePatcher):

    def __init__(self):
        super(QmdbPatcher, self).__init__('movie')


class QsdbPather(BasePatcher):

    def __init__(self):
        super(QsdbPather, self).__init__('karaoke')


class QadbPatch(BasePatcher):

    def __init__(self):
        super(QadbPatch, self).__init__('av')


class MoviesPatcher(QmdbPatcher):

    def _set_tablename(self):
        return 'movies'

    def get_columns(self):
        return ('id', 'source', 'title', 'akas', 'kind', 'genres', 'u_genres', 'runtimes', 'rating', 'thumbnailurl',
                'posterurl', 'directors', 'writers', 'stars', 'year', 'releasedate', 'countries', 'u_countries',
                'languages', 'u_languages', 'description', 'imdbid', 'url', 'vcount', 'dcount', 'pcount', 'total_count',
                'udate', 'md5sum')

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_movies;
        CREATE TABLE temp_movies
        (
          id varchar(20) NOT NULL,
          source varchar(10) NOT NULL,
          title varchar(512) NOT NULL,
          akas varchar(512)[],
          kind varchar(10),
          genres varchar(20)[],
          u_genres varchar(10)[],
          runtimes integer,
          rating real,
          thumbnailurl varchar(2048),
          posterurl varchar(2048),
          directors varchar(128)[],
          writers varchar(128)[],
          stars varchar(128)[],
          year integer,
          releasedate json,
          countries varchar(64)[],
          u_countries varchar(64)[],
          languages varchar(64)[],
          u_languages varchar(64)[],
          description text,
          imdbid varchar(9),
          url varchar(2048),
          vcount integer DEFAULT 0,
          dcount integer DEFAULT 0,
          pcount integer DEFAULT 0,
          total_count integer DEFAULT 0,
          udate timestamp without time zone,
          md5sum varchar(32)
        );
        """

    def _set_sqlcmd(self):
        return """
        LOCK TABLE movies IN SHARE ROW EXCLUSIVE MODE;
        with upsert as (
            update movies set source=t.source, title=t.title, akas=t.akas, kind=t.kind, genres=t.genres,
            u_genres=t.u_genres, runtimes=t.runtimes, rating=t.rating, thumbnailurl=t.thumbnailurl,
            posterurl=t.posterurl, directors=t.directors, writers=t.writers, stars=t.stars, year=t.year,
            releasedate=t.releasedate, countries=t.countries, u_countries=t.countries, languages=t.languages,
            u_languages=t.u_languages, description=t.description, imdbid=t.imdbid, url=t.url, udate=t.udate,
            md5sum=t.md5sum
            from temp_movies t
            where t.id = movies.id
            RETURNING t.id
        )
        insert into movies(id, source, title, akas, kind, genres, u_genres, runtimes, rating, thumbnailurl, posterurl,
        directors, writers, stars, year, releasedate, countries, u_countries, languages, u_languages, description,
        imdbid, url, udate, md5sum)
        select id, source, title, akas, kind, genres, u_genres, runtimes, rating, thumbnailurl, posterurl,
        directors, writers, stars, year, releasedate, countries, u_countries, languages, u_languages, description,
        imdbid, url, udate, md5sum
        from temp_movies where id not in (select id from upsert);

        -- update rating by imdb rating
        update movies set rating=m.rating from movies m
        where movies.source != 'imdb'
        and m.source = 'imdb'
        and movies.imdbid=m.imdbid
        and m.rating is not null;

        -- clear duplicate imdbid(atmovies)
        %(clear_atmoives_imdbid)s

        -- clear duplicated imdbid(douban)
        %(clear_douban_imdbid)s
        """ % {
            'clear_atmoives_imdbid': self.clear_duplicate_imdbid_sql(source='atmovies'),
            'clear_douban_imdbid': self.clear_duplicate_imdbid_sql(source='douban'),
        }

    def clear_duplicate_imdbid_sql(self, source):
        return """
        update movies set imdbid = null
        where source = '%(source)s' and imdbid in (
        select imdbid from movies
        where source = '%(source)s'
        and imdbid is not null
        group by imdbid
        having count(*) > 1
        );
        """ % {'source': source}


class MovieContentPatcher(QmdbPatcher):

    def _set_tablename(self):
        return 'movie_content'

    def get_columns(self):
        return (
            'id', 'source', 'title', 'akas', 'year', 'imdbid', 'info_url', 'content_url', 'udate', 'md5sum'
        )

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_movie_content;
        CREATE TABLE temp_movie_content
        (
          id varchar(20) NOT NULL,
          source varchar(10) NOT NULL,
          title varchar(128) NOT NULL,
          akas varchar(256)[],
          year integer,
          imdbid varchar(9),
          info_url varchar(2048),
          content_url varchar(2048),
          udate timestamp without time zone,
          md5sum varchar(32) NOT NULL
        );
        """

    def _set_sqlcmd(self):
        return """
        LOCK TABLE movie_content IN SHARE ROW EXCLUSIVE MODE;
        with upsert as (
            update movie_content set source=t.source, title=t.title, akas=t.akas, year=t.year, info_url=t.info_url,
            content_url=t.content_url, udate=t.udate, md5sum=t.md5sum
            from temp_movie_content t
            where t.id = movie_content.id
            RETURNING t.id
        )
        insert into movie_content(id, source, title, akas, year, imdbid, info_url, content_url, udate, md5sum)
        select id, source, title, akas, year, imdbid, info_url, content_url, udate, md5sum
        from temp_movie_content where id not in (select id from upsert);

        update movie_content set imdbid = movies.imdbid
        from movies
        where movie_content.title = movies.title
        and movie_content.year = movies.year
        and movie_content.imdbid is null
        and movies.imdbid is not null;
        """


class SongsPatcher(QsdbPather):

    def _set_tablename(self):
        return 'songs'

    def get_columns(self):
        return (
            'source', 'title', 'lang', 'artist', 'keywords', 'keymd5', 'udate'
        )

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_songs;
        CREATE TABLE temp_songs
        (
          source varchar(20) NOT NULL, -- 來源(cashbox...)
          title varchar(256) NOT NULL, -- 歌名
          lang varchar(8), -- 語言, M:國語/E:英語/T:台語/C:粤語/J:日語/K:/韓語/THA:泰語
          artist varchar(128), -- 歌手
          keywords varchar(256), -- 將歌名及歌手轉小寫、繁體，將符號以空白取代，再用空白做分隔轉成list，用字母排序後再轉字串；例"心時代 畢書盡、陳勢安、陳彥允、李玉璽"變"心時代 畢書盡 陳勢安 陳彥允 李玉璽"
          keymd5 varchar(32) NOT NULL, -- 將keywords算md5
          udate timestamp without time zone -- 更新時間
        );
        """

    def _set_sqlcmd(self):
        return """
        LOCK TABLE songs IN SHARE ROW EXCLUSIVE MODE;
        with upsert as (
            update songs set source=t.source, title=t.title, lang=t.lang, artist=t.artist, keywords=t.keywords,
            keymd5=t.keymd5, udate=t.udate
            from temp_songs t
            where t.keymd5 = songs.keymd5
            RETURNING t.keymd5
        )
        insert into songs(source, title, lang, artist, keywords, keymd5, udate)
        select source, title, lang, artist, keywords, keymd5, udate
        from temp_songs where keymd5 not in (select keymd5 from upsert);
        """


class SonglistPatcher(QsdbPather):

    def _set_tablename(self):
        return 'song_list'

    def get_columns(self):
        return (
            'source', 'type', 'lang', 'title', 'artist', 'rank', 'keymd5', 'udate'
        )

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_song_list;
        CREATE TABLE temp_song_list
        (
          source varchar(10) NOT NULL, -- 來源
          type character(1) NOT NULL, -- 類別, 1:新歌/2:點播排行/3:新歌排行
          lang varchar(8), -- 語言, M:國語/E:英語/T:台語/C:粤語/J:日語
          title varchar(256) NOT NULL, -- 歌名
          artist varchar(128), -- 歌手
          rank integer,
          keymd5 varchar(32) NOT NULL, -- same as sonsgs.md5sum
          udate timestamp without time zone -- 更新時間
        );
        """

    def _set_sqlcmd(self):
        return """
        truncate table song_list;
        insert into song_list(source, type, lang, title, artist, rank, keymd5, udate)
        select source, type, lang, title, artist, rank, keymd5, udate
        from temp_song_list;
        """


class SongcontentPatcher(QsdbPather):

    def _set_tablename(self):
        return 'song_content'

    def get_columns(self):
        return (
            'source', 'fullname', 'poster_url', 'uploader', 'upload_date', 'description', 'duration', 'play_url',
            'content', 'keymd5', 'md5sum', 'udate'
        )

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_song_content;
        CREATE TABLE temp_song_content
        (
          source varchar(10) NOT NULL, -- 來源(youtube, bt)
          fullname varchar(256) NOT NULL, -- 來源歌曲全名
          poster_url varchar(2048), -- 封面網址
          uploader varchar(128), -- 上傳者
          upload_date varchar(32), -- 上傳日期
          description text, -- 簡介
          duration integer, -- 長度
          play_url varchar(2048), -- 影片播放網址
          content json, -- 磁力連結或youtube的format資訊
          keymd5 varchar(32) NOT NULL, -- same as sonsgs.md5sum
          md5sum varchar(32), -- content md5sum
          udate timestamp without time zone -- 更新時間
        );
        """

    def _set_sqlcmd(self):
        return """
        LOCK TABLE songs IN SHARE ROW EXCLUSIVE MODE;
        with upsert as (
            update song_content set source=t.source, fullname=t.fullname, poster_url=t.poster_url, uploader=t.uploader,
            upload_date=t.upload_date, description=t.description, duration=t.duration, play_url=t.play_url,
            content=t.content, keymd5=t.keymd5, md5sum=t.md5sum, udate=t.udate
            from temp_song_content t
            where t.source = song_content.source and t.keymd5 = song_content.keymd5
            RETURNING t.source, t.keymd5
        )
        insert into song_content(source, fullname, poster_url, uploader, upload_date, description, duration, play_url,
        content, keymd5, md5sum, udate)
        select source, fullname, poster_url, uploader, upload_date, description, duration, play_url,
        content, keymd5, md5sum, udate
        from temp_song_content where not exists (
            select keymd5 from upsert
            where source=temp_song_content.source
            and keymd5=temp_song_content.keymd5
        );
        """


class AvVideoPatcher(QadbPatch):

    def _set_tablename(self):
        return 'video'

    def get_columns(self):
        return (
            'id', 'code', 'title', 'posterurl', 'duration', 'performer', 'category', 'rating', 'maker', 'series', 'date',
            'date2', 'description', 'samples', 'url', 'md5sum', 'udate'
        )

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_video;
        Create table temp_video(
            id varchar(32) not null, -- dmm品番
            code varchar(32) null, -- 番號
            title varchar(256) not null, --片名
            posterurl varchar(2048), -- 封面
            duration integer, -- 片長
            performer varchar(64)[], -- 出演者
            category varchar(128)[], -- 類別
            rating real, -- 評分
            maker varchar(32), -- 廠商
            series varchar(128), -- 系列
            date timestamp, -- 商品発売日
            date2 timestamp, -- 配信開始日
            description text, -- 簡介
            samples varchar(2048)[], -- 截圖
            url varchar(2048) not null, -- 網址
            md5sum varchar(32) not null,
            udate timestamp -- 更新時間
        );
        """

    def _set_sqlcmd(self):
        return """
        LOCK TABLE video IN SHARE ROW EXCLUSIVE MODE;
        with upsert as (
            update video set code=t.code, title=t.title, posterurl=t.posterurl, duration=t.duration, performer=t.performer,
            category=t.category, rating=t.rating, maker=t.maker, series=t.series, date=t.date,
            description=t.description, samples=t.samples, url=t.url, md5sum=t.md5sum, udate=t.udate
            from temp_video t
            where t.id = video.id
            RETURNING t.id
        )
        insert into video(id, code, title, posterurl, duration, performer, category, rating, maker, series, date, description,
        samples, url, md5sum, udate)
        select id, code, title, posterurl, duration, performer, category, rating, maker, series, date, description, samples,
        url,md5sum, udate
        from temp_video where not exists (
            select id from upsert
            where id=temp_video.id
        );
        """


class DramaPatcher(QmdbPatcher):

    def _set_tablename(self):
        return 'drama'

    def get_columns(self):
        return (
            'id', 'source', 'title', 'akas', 'kind', 'genres', 'posterurl', 'stars', 'year', 'region', 'description',
            'url', 'play_urls', 'update_eps', 'total_eps', 'completed',  'vcount', 'dcount', 'pcount', 'rdate',
            'udate', 'md5sum', 'total_count', 'dbid'
        )

    def _set_temp_table_sqlcmd(self):
        return """
        Drop table if exists temp_drama;
        Create table temp_drama(
            id varchar(20) NOT NULL, -- kb_+kuboID
            source varchar(10) NOT NULL, -- 來源(kubo)
            title varchar(512) NOT NULL,
            akas varchar(256)[], -- 別名
            kind varchar(10), -- 種類(0/動畫,1/台劇,2/韓劇,3/日劇,4/陸劇,5/港劇,6/美劇,7/其他,8/布袋戲
            genres varchar(20)[], -- 類型(推理、恐怖...)
            posterurl varchar(200), -- 封面網址
            stars varchar(128)[], -- 演員
            year integer,
            region varchar(64), -- 地區
            description text, -- 劇情
            url varchar(2048), -- metadata來源網址
            play_urls json, -- 影片網址
            update_eps int, -- 更新的集數
            total_eps int, -- 全部集數
            completed bool, -- 是否完結
            vcount integer DEFAULT 0, -- 在client查看的次數
            dcount integer DEFAULT 0, -- 在client下載的次數
            pcount integer DEFAULT 0, -- 在client播放的次數
            rdate varchar(20) NOT NULL, -- kubo更新時間
            udate timestamp without time zone, -- 更新時間
            md5sum varchar(32),
            total_count integer DEFAULT 0,
            dbid varchar(20) -- 豆瓣id
        );
        """

    def _set_sqlcmd(self):
        return """
        LOCK TABLE drama IN SHARE ROW EXCLUSIVE MODE;
        with upser as (
            update drama set source=t.source, title=t.title, akas=t.akas, kind=t.kind, genres=t.genres,
            posterurl=t.posterurl, stars=t.stars, year=t.year, region=t.region, description=t.description, url=t.url,
            play_urls=t.play_urls, update_eps=t.update_eps, total_eps=t.total_eps, completed=t.completed, rdate=t.rdate,
            udate=t.udate, md5sum=t.md5sum, dbid=t.dbid
            from temp_drama t
            where t.id = drama.id
            Returning t.id
        )
        insert into drama(id, source, title, akas, kind, genres, posterurl, stars, year, region, description, url,
        play_urls, update_eps, total_eps, completed, rdate, udate, md5sum, dbid)
        select id, source, title, akas, kind, genres, posterurl, stars, year, region, description, url,
        play_urls, update_eps, total_eps, completed, rdate, udate, md5sum, dbid
        from temp_drama where not exists(
            select id from upser
            where id=temp_drama.id
        );

        -- clear duplicated dbid(kubo)
        update drama set dbid = null
        where source = 'kubo' and dbid in (
        select dbid from drama
        where source = 'kubo'
        and dbid is not null
        group by dbid
        having count(*) > 1
        );

        -- clear null dbid drama
        delete from drama where source = 'douban' and dbid is null;
        delete from drama where source = 'imdb' and dbid is null;

        -- update posterurl(imdb)
        %(update_imdb_posterurl_from_kubo)s
        %(update_imdb_posterurl_from_douban)s

        -- update posterurl(kubo)
        %(update_kubo_posterurl_from_douban)s
        %(update_kuob_posterurl_from_imdb)s

        -- update posterurl(douban)
        %(update_douban_posterurl_from_kubo)s
        %(update_douban_posterurl_from_imdb)s
        """ % {
            'update_imdb_posterurl_from_kubo': self._update_posterurl_sql(from_source='kubo', target_source='imdb'),
            'update_imdb_posterurl_from_douban': self._update_posterurl_sql(from_source='douban', target_source='imdb'),
            'update_kubo_posterurl_from_douban': self._update_posterurl_sql(from_source='douban', target_source='kubo'),
            'update_kuob_posterurl_from_imdb': self._update_posterurl_sql(from_source='imdb', target_source='kubo'),
            'update_douban_posterurl_from_kubo': self._update_posterurl_sql(from_source='kubo', target_source='douban'),
            'update_douban_posterurl_from_imdb': self._update_posterurl_sql(from_source='imdb', target_source='douban'),
        }

    def _update_posterurl_sql(self, from_source, target_source):
        return """
        update drama set posterurl=d.posterurl from drama d
        where drama.dbid = d.dbid
        and drama.source = '%(target)s'
        and d.source = '%(from)s'
        and drama.posterurl is null
        and d.posterurl is not null;
        """ % {
            'from': from_source,
            'target': target_source
        }
