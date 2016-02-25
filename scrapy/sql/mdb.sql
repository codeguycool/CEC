Drop extension if exists pg_trgm;
Create extension pg_trgm;

-- 電影資料來源(metadata), 如果有變更, temp_movies也要一併變更

Drop table if exists movies;
Create table movies
(
  id varchar(20) not null, -- am_+AtMoviesID/db_+DoubanID/im_+IMDBID max:12
  source varchar(10) not null, -- 來源(atmovies/douban/imdb)
  title varchar(512) not null, -- title max:188(""1971, of zelfs al houdt Mosje Dajan zijne kak in en komt er voor 1971 genen oorlog, dan nog zal de Belgische film, dank zij de huidige situatie (om het kort te zeggen) er als volgt uitzien"")
  akas varchar(512)[], -- 別名 max:208(""恶魔、变异人、异形、食人魔、地狱边缘的僵尸化的活死人携妻带子大举归来恐怖进攻不分日夜杀出个黎明2：极度震惊2D版"")
  kind varchar(10), -- 種類(movie, tv, anima, mv, other)
  genres varchar(20)[], -- 類型(raw), max("{"紀錄片 Documentary"}")
  u_genres varchar(10)[], -- 類型(unified)
  runtimes integer, -- 片長
  rating real, -- 評分
  posterurl varchar(2048), -- 海報網址 max:106
  directors varchar(128)[], -- 導演 max:53(艾雷斯泰·法瑟吉尔 Alastair Fothergill ....(11 episodes, 2006)) "10462917"
  writers varchar(128)[], -- 編劇
  stars varchar(128)[], -- 演員
  year integer,
  releaseDate json, -- 上映日期 {'中国大陆': '2015-01-08'}
  countries varchar(64)[], -- 出品國(raw) max:22(Bosnia and Herzegovina)
  u_countries varchar(64)[], -- 出品國(unified)
  languages varchar(64)[], -- 語言(raw)
  u_languages varchar(64)[], -- 語言(unified)
  description text, -- 劇情
  imdbid varchar(9),
  url varchar(2048), -- max:79
  vcount integer default(0), -- 在qpkg查看的次數
  dcount integer default(0), -- 在qpkg下載的次數
  pcount integer default(0), -- 在qpkg播放的次數
  total_count integer DEFAULT(0), -- vcount, dcount, pcount 的總和
  md5sum varchar(32) not null,
  udate timestamp, -- 更新時間
  Constraint "movies_pk" Primary Key ("id")
);

Create Index movies_idx_source
  On movies
  Using BTree
  (source);

Create Index movies_idx_title
  On movies
  Using BTree
  (title);

Create Index movies_idx_year
  On movies
  Using BTree
  (year);

Create Index movies_idx_imdbid
  On movies
  Using BTree
  (imdbid);

Comment on Column movies.id is'am_+AtMoviesID/db_+DoubanID/im_+IMDBID';
Comment on Column movies.source is'來源(atmovies/douban/imdb)';
Comment on Column movies.akas is'別名';
Comment on Column movies.kind is'種類(movie, tv, anima, mv, other)';
Comment on Column movies.genres is'類型(raw)';
Comment on Column movies.u_genres is'類型(unified)';
Comment on Column movies.runtimes is'片長';
Comment on Column movies.rating is'評分';
Comment on Column movies.posterurl is'海報網址';
Comment on Column movies.directors is'導演';
Comment on Column movies.writers is'編劇';
Comment on Column movies.stars is'演員';
Comment on Column movies.releaseDate is'上映日期';
Comment on Column movies.countries is'出品國(raw)';
Comment on Column movies.u_countries is'出品國(unified)';
Comment on Column movies.languages is'語言(raw)';
Comment on Column movies.u_languages is'語言(unified)';
Comment on Column movies.description is'劇情';
Comment on Column movies.vcount is'在qpkg查看的次數';
Comment on Column movies.dcount is'在qpkg下載的次數';
Comment on Column movies.pcount is'在qpkg播放的次數';
Comment on Column movies.total_count is'vcount, dcount, pcount 的總和';
Comment on Column movies.udate is'更新時間';



-- 暫存 movies table, 用來更新 cloud 上的 movies table 之用, 如果 movies table 有變更, temp_movies 也要一併變更
-- 不需要pcount, vcount, dcount, total_count 欄位

Drop table if exists temp_movies;
CREATE TABLE temp_movies
(
  id character varying(20) NOT NULL,
  source character varying(10) NOT NULL,
  title character varying(512) NOT NULL,
  akas character varying(512)[],
  kind character varying(10),
  genres character varying(20)[],
  u_genres character varying(10)[],
  runtimes integer,
  rating real,
  posterurl character varying(2048),
  directors character varying(128)[],
  writers character varying(128)[],
  stars character varying(128)[],
  year integer,
  releasedate json,
  countries character varying(64)[],
  u_countries character varying(64)[],
  languages character varying(64)[],
  u_languages character varying(64)[],
  description text,
  imdbid character varying(9),
  url character varying(2048),
  vcount integer default(0), -- 在qpkg查看的次數
  dcount integer default(0), -- 在qpkg下載的次數
  pcount integer default(0), -- 在qpkg播放的次數
  total_count integer DEFAULT(0), -- vcount, dcount, pcount 的總和
  udate timestamp without time zone,
  md5sum character varying(32),
  CONSTRAINT "movie_pk_id" PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE temp_movies
  OWNER TO postgres;



-- 電影活動統計

Drop table if exists movie_statistics;
Create table movie_statistics
(
  id uuid,
  movieid varchar(20) not null, -- 'same as Movie.id'
  imdbid varchar(9),
  type char(1), -- d:download/v:view/p:play
  datetime timestamp,
  Constraint "movie_statistics_pk" Primary Key("id")
);

Create index movie_statistics_idx_imdbid
  on movie_statistics
  using btree(imdbid);

Comment on Column movie_statistics.movieid is'same as Movie.id';
Comment on Column movie_statistics.type is'd:download/v:view/p:play';



-- 最新電影

Drop table if exists movie_latest;
Create table movie_latest
(
  imdbid varchar(9) not null,
  Constraint "movie_latest_pk" Primary Key("imdbid")
);



-- 電影檔案來源(content), 如果有變更, temp_movie_content 也要一併變更

Drop table if exists movie_content;
Create table movie_content
(
  id varchar(20) not null, -- td_+TudouID/yk_+YoukuID
  source varchar(10) not null, -- 來源(todou/youku)
  title varchar(128) not null,
  akas varchar(256)[], -- 別名
  year integer,
  imdbid varchar(9),
  info_url varchar(2048), -- 檔案資訊頁url
  content_url varchar(2048), -- 檔案播放頁url
  md5sum varchar(32) not null,
  udate timestamp, -- 更新時間
  Constraint "movie_content_px" Primary Key ("id")
);

Create Index movie_content_idx_source
  On movie_content
  Using BTree
  (source);

Create Index movie_content_idx_title
  On movie_content
  Using BTree
  (title);

Create Index movie_content_idx_year
  On movie_content
  Using BTree
  (year);

Create Index movie_content_idx_imdbid
  On movie_content
  Using BTree
  (imdbid);

Comment on Column movie_content.id is'td_+TudouID/yk_+YoukuID';
Comment on Column movie_content.source is'來源(todou/youku)';
Comment on Column movie_content.akas is'別名';
Comment on Column movie_content.info_url is'檔案資訊頁url';
Comment on Column movie_content.content_url is'檔案播放頁url';
Comment on Column movie_content.udate is'更新時間';



-- 暫存 movie_content table, 用來更新 cloud 上的 movie_content table 之用, 如果 movie_content 有變更, temp_movie_content 也要一併變更

Drop table if exists temp_movie_content;
CREATE TABLE temp_movie_content
(
  id character varying(20) NOT NULL,
  source character varying(10) NOT NULL,
  title character varying(128) NOT NULL,
  akas character varying(256)[],
  year integer,
  imdbid character varying(9),
  info_url character varying(2048),
  content_url character varying(2048),
  udate timestamp without time zone,
  md5sum character varying(32) NOT NULL,
  CONSTRAINT "temp_movie_cotnent_pk_id" PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE temp_movie_content
  OWNER TO postgres;



-- movie_keyword

Drop table if exists movie_keyword;
Create table movie_keyword
(
  id varchar(20) not null, -- 'same as movies.id';
  source varchar(10) not null, -- 來源(atmovies/douban/imdb)
  kind varchar(10), -- 種類(movie, tv, anima, mv, other)
  keywords text, -- keywords(title, aks, director, writer, start, year, description)
  imdbid varchar(9),
  Constraint "movie_keyword_pk" Primary Key ("id")
);

Comment on Column movie_keyword.id is'same as movies.id';
Comment on Column movie_keyword.source is'來源(atmovies/douban/imdb)';
Comment on Column movie_keyword.kind is'種類(movie, tv, anima, mv, other)';
Comment on Column movie_keyword.keywords is'keywords(title, aks, director, writer, start, year, description)';

Create Index movie_keyword_idx_source
  On movie_keyword
  Using btree
  (source);

Create Index movie_keyword_idx_keyword
  On movie_keyword
  Using gin
  (keywords gin_trgm_ops);



-- BT天堂

Drop table if exists bttt;
Create table bttt
(
  id varchar(10) not null,
  title varchar(256) not null,
  imdbid varchar(9),
  info_url varchar(2048) not null, -- bt天堂資訊頁, http://www.bttiantang.com/subject/27151.html
  content_urls json, -- bt種子網址
  udate varchar(20) not null, -- 更新日期, e.g. 2012/03/20
  Constraint "bttt_pk" Primary Key("id")
);

Comment on Column bttt.info_url is'bt天堂資訊頁, http://www.bttiantang.com/subject/27151.html';
Comment on Column bttt.content_urls is'bt種子網址';
Comment on Column bttt.udate is'bt天堂更新日期, e.g. 2012/03/20';

Create Index bttt_idx_imdbid
  on bttt
  using BTree
  (imdbid);

Create Index bttt_idx_udate
  on bttt
  using BTree
  (udate);
