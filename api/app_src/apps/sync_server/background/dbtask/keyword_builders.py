# -*-coding: utf-8 -*-

""" keyword builder factory

set builder variables(sqlcmd, db....)

"""

from build_keyword_task import BuildKeywordTask
from framework.sys_tools import g


def create_keyword_builder(tablename):
    """ factory method

    :param tablename:
    :return:
    """
    builders = {
        'movies': MoviesBuilder,
        'video': AvBuilder,
        'drama': DramaBuilder
    }
    builder = builders.get(tablename, None)
    return builder() if builder else None


class BaseBuilder(object):

    def __init__(self, db):
        if db is None:
            raise ValueError('db is None')
        self.db = db
        self.sqlcmd = self._set_sqlcmd()

    def get_db(self):
        return self.db

    def get_tablename(self):
        raise NotImplementedError

    def _set_sqlcmd(self):
        raise NotImplementedError

    def build(self, taskname):
        bg_task = BuildKeywordTask(self.db, self.sqlcmd)
        g().set(taskname, bg_task)
        bg_task.start()


class MoviesBuilder(BaseBuilder):

    def __init__(self):
        super(MoviesBuilder, self).__init__('movie')

    def get_tablename(self):
        return 'movie_keyword'

    def _set_sqlcmd(self):
        return u"""
        -- create temp table
        Drop table if exists movie_keyword2;
        CREATE TABLE movie_keyword2
        (
          id varchar(20) NOT NULL, -- same as Movie.id
          kind varchar(10), -- 種類(movie, tv, other)
          keywords text NOT NULL, -- keywords(title, aks, genres, year, director, starts, countries, description)
          j_tsv tsvector,
          imdbid varchar(9),
          source varchar(10),
          CONSTRAINT movie_keyword2_pk PRIMARY KEY (id)
        );

        COMMENT ON COLUMN movie_keyword2.id IS 'same as Movie.id';
        COMMENT ON COLUMN movie_keyword2.kind IS '種類(movie, tv, other)';
        COMMENT ON COLUMN movie_keyword2.keywords IS 'keywords(title, aks, genres, year, director, starts, countries, description)';


        -- insert keyword
        set local maintenance_work_mem = '256MB';

        insert into movie_keyword2(id, source, kind, keywords, j_tsv, imdbid)
        select id, source, kind, left(concat(title)
        || ' ' || array_to_string(akas, ' ')
        || ' ' || array_to_string(genres, ' ')
        || ' ' || concat(year)
        || ' ' || array_to_string(directors, ' ')
        || ' ' || array_to_string(stars, ' ')
        || ' ' || array_to_string(countries, ' ')
        || ' ' || concat(description), 2700),
        to_tsvector('jiebacfg',
        left(concat(title)
        || ' ' || array_to_string(akas, ' ')
        || ' ' || array_to_string(genres, ' ')
        || ' ' || concat(year)
        || ' ' || array_to_string(directors, ' ')
        || ' ' || array_to_string(stars, ' ')
        || ' ' || array_to_string(countries, ' ')
        || ' ' || concat(description), 2700)),
        imdbid
        from movies;

        Create Index movie_keyword2_idx_source
          On movie_keyword2
          Using btree
          (source);

        Create Index movie_keyword2_idx_keyword
          On movie_keyword2
          Using gin
          (keywords gin_trgm_ops);

        CREATE INDEX movie_keyword2_j_tsv
          ON movie_keyword2
          USING gin
          (j_tsv);

        -- drop & rename
        drop table if exists movie_keyword;
        alter table movie_keyword2 rename to movie_keyword;
        alter index movie_keyword2_pk rename to movie_keyword_pk;
        alter index movie_keyword2_idx_source rename to movie_keyword_idx_source;
        alter index movie_keyword2_idx_keyword rename to movie_keyword_idx_keyword;
        alter index movie_keyword2_j_tsv rename to movie_keyword_j_tsv;
        """


class AvBuilder(BaseBuilder):

    def __init__(self):
        super(AvBuilder, self).__init__('av')

    def get_tablename(self):
        return 'video_keyword'

    def _set_sqlcmd(self):
        return u"""
        -- create temp table
        Drop Table if exists video_keyword2;
        Create table video_keyword2
        (
            id varchar(32) not null, -- 'same as video.id'
            keywords text, -- keywords(id, title, performer, category, maker, series)
            Constraint "video_keyword2_pk" Primary Key ("id")
        );

        Comment on Column video_keyword2.id is'same as video.id';
        Comment on Column video_keyword2.keywords is'keywords(id, title, performer, category, maker, series)';


        -- insert keyword
        set local maintenance_work_mem = '256MB';

        insert into video_keyword2(id, keywords)
        select id, left(concat(id)
        || ' ' || concat(code)
        || ' ' || concat(title)
        || ' ' || concat(performer)
        || ' ' || array_to_string(category, ' ')
        || ' ' || concat(maker)
        || ' ' || concat(series)
        || ' ' || concat(description), 2700)
        from video;

        CREATE INDEX video_keyword2_idx_keyword
          ON video_keyword2
          USING gin
          (keywords COLLATE pg_catalog."default" gin_trgm_ops);


        -- drop & rename
        drop table if exists video_keyword;
        alter table video_keyword2 rename to video_keyword;
        alter index video_keyword2_pk rename to video_keyword_pk;
        alter index video_keyword2_idx_keyword rename to video_keyword_idx_keyword;
        """


class DramaBuilder(BaseBuilder):

    def __init__(self):
        super(DramaBuilder, self).__init__('movie')

    def get_tablename(self):
        return 'drama_keyword'

    def _set_sqlcmd(self):
        return u"""
        -- create temp table
        Drop Table if exists drama_keyword2;
        Create table drama_keyword2
        (
            id varchar(20) not null, -- 'same as drama.id'
            source varchar(10),
            dbid character varying(20), -- 豆瓣id
            keywords text, -- keywords(title, akas, genres, stars, region, description)
            Constraint "drama_keyword2_pk" Primary Key ("id")
        );

        Comment on Column drama_keyword2.id is'same as drama.id';
        Comment on Column drama_keyword2.dbid is'豆瓣id';
        Comment on Column drama_keyword2.keywords is'keywords(title, akas, genres, stars, region, description)';


        -- insert data
        set local maintenance_work_mem = '256MB';

        insert into drama_keyword2(id, source, dbid, keywords)
        select id, source, dbid, left(concat(title)
        || ' ' || array_to_string(akas, ' ')
        || ' ' || array_to_string(genres, ' ')
        || ' ' || array_to_string(stars, ' ')
        || ' ' || concat(region)
        || ' ' || concat(description), 2700)
        from drama;

        Create Index drama_keyword2_idx_source
          On drama_keyword2
          Using btree
          (source);

        CREATE INDEX drama_keyword2_idx_keyword
          ON drama_keyword2
          USING gin
          (keywords COLLATE pg_catalog."default" gin_trgm_ops);


        -- drop & rename
        drop table if exists drama_keyword;
        alter table drama_keyword2 rename to drama_keyword;
        alter index drama_keyword2_pk rename to drama_keyword_pk;
        alter index drama_keyword2_idx_source rename to drama_kewword_idx_source;
        alter index drama_keyword2_idx_keyword rename to drama_keyword_idx_keyword;
        """
