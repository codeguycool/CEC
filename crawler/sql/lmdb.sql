-- local movies database

-- trigram extension
Create extension if not exists pg_trgm;

-- 電影資訊(開眼、豆瓣、yes電影、IMDB)

CREATE TABLE movies
(
  id varchar(20) NOT NULL, -- am_+AtMoviesID/db_+DoubanID/im_+IMDBID
  source varchar(10) NOT NULL, -- 來源(atmovies/douban/imdb)
  title varchar(512) NOT NULL,
  akas varchar(512)[], -- 別名
  kind varchar(10), -- 種類(movie, tv, anima, mv, other)
  genres varchar(20)[], -- 類型(raw)
  u_genres varchar(10)[], -- 類型(unified)
  runtimes integer, -- 片長
  rating real, -- 評分
  posterurl varchar(2048), -- 海報網址
  thumbnailurl varchar(2048), -- 海報縮圖網址
  directors varchar(128)[], -- 導演
  writers varchar(128)[], -- 編劇
  stars varchar(128)[], -- 演員
  year integer,
  releasedate json, -- 上映日期
  countries varchar(64)[], -- 出品國(raw)
  u_countries varchar(64)[], -- 出品國(unified)
  languages varchar(64)[], -- 語言(raw)
  u_languages varchar(64)[], -- 語言(unified)
  description text, -- 劇情
  imdbid varchar(9),
  url varchar(2048),
  vcount integer DEFAULT 0, -- 查看的次數
  dcount integer DEFAULT 0, -- 下載的次數
  pcount integer DEFAULT 0, -- 播放的次數
  udate timestamp without time zone, -- 更新時間
  md5sum varchar(32),
  total_count integer DEFAULT 0,
  CONSTRAINT "pk_movies" PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE movies
  OWNER TO postgres;


COMMENT ON COLUMN movies.id IS 'am_+AtMoviesID/db_+DoubanID/im_+IMDBID';
COMMENT ON COLUMN movies.source IS '來源(atmovies/douban/imdb)';
COMMENT ON COLUMN movies.akas IS '別名';
COMMENT ON COLUMN movies.kind IS '種類(movie, tv, anima, mv, other)';
COMMENT ON COLUMN movies.genres IS '類型(raw)';
COMMENT ON COLUMN movies.u_genres IS '類型(unified)';
COMMENT ON COLUMN movies.runtimes IS '片長';
COMMENT ON COLUMN movies.rating IS '評分';
COMMENT ON COLUMN movies.posterurl IS '海報網址';
COMMENT ON COLUMN movies.thumbnailurl IS '海報縮圖網址';
COMMENT ON COLUMN movies.directors IS '導演';
COMMENT ON COLUMN movies.writers IS '編劇';
COMMENT ON COLUMN movies.stars IS '演員';
COMMENT ON COLUMN movies.releasedate IS '上映日期';
COMMENT ON COLUMN movies.countries IS '出品國(raw)';
COMMENT ON COLUMN movies.u_countries IS '出品國(unified)';
COMMENT ON COLUMN movies.languages IS '語言(raw)';
COMMENT ON COLUMN movies.u_languages IS '語言(unified)';
COMMENT ON COLUMN movies.description IS '劇情';
COMMENT ON COLUMN movies.vcount IS '查看的次數';
COMMENT ON COLUMN movies.dcount IS '下載的次數';
COMMENT ON COLUMN movies.pcount IS '播放的次數';
COMMENT ON COLUMN movies.udate IS '更新時間';


CREATE INDEX movie_imdbid_idx
  ON movies
  USING btree
  (imdbid COLLATE pg_catalog."default");

CREATE INDEX movie_source_idx
  ON movies
  USING btree
  (source COLLATE pg_catalog."default");

CREATE INDEX movie_title_idx
  ON movies
  USING btree
  (title COLLATE pg_catalog."default");

CREATE INDEX movie_year_idx
  ON movies
  USING btree
  (year);

CREATE INDEX movies_idx_udate
  ON movies
  USING btree
  (udate DESC);


-- 電影影片(土豆)

CREATE TABLE movie_content
(
  id varchar(20) NOT NULL, -- td_+TudouID/yk_+YoukuID
  source varchar(10) NOT NULL, -- 來源(todou/youku)
  title varchar(128) NOT NULL,
  akas varchar(256)[], -- 別名
  year integer,
  imdbid varchar(9),
  info_url varchar(2048), -- 檔案資訊頁url
  content_url varchar(2048), -- 檔案播放頁url
  udate timestamp without time zone, -- 更新時間
  md5sum varchar(32),
  CONSTRAINT "pk_MovieContent" PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE movie_content
  OWNER TO postgres;


COMMENT ON COLUMN movie_content.id IS 'td_+TudouID/yk_+YoukuID';
COMMENT ON COLUMN movie_content.source IS '來源(todou/youku)';
COMMENT ON COLUMN movie_content.akas IS '別名';
COMMENT ON COLUMN movie_content.info_url IS '檔案資訊頁url';
COMMENT ON COLUMN movie_content.content_url IS '檔案播放頁url';
COMMENT ON COLUMN movie_content.udate IS '更新時間';


CREATE INDEX movie_content_idx_imdbid
  ON movie_content
  USING btree
  (imdbid COLLATE pg_catalog."default");

CREATE INDEX movie_content_idx_source
  ON movie_content
  USING btree
  (source COLLATE pg_catalog."default");

CREATE INDEX movie_content_idx_title
  ON movie_content
  USING btree
  (title COLLATE pg_catalog."default");

CREATE INDEX movie_content_idx_year
  ON movie_content
  USING btree
  (year);


-- 搜尋關鍵字

CREATE TABLE movie_keyword
(
  id varchar(20) NOT NULL, -- same as Movie.id
  kind varchar(10), -- 種類(movie, tv, other)
  keywords text NOT NULL, -- keywords(title, aks, genres, year, director, starts, countries, description)
  j_tsv tsvector, -- 結巴的tsvector
  imdbid varchar(9),
  source varchar(10),
  CONSTRAINT movie_keyword_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE movie_keyword
  OWNER TO postgres;


COMMENT ON COLUMN movie_keyword.id IS 'same as Movie.id';
COMMENT ON COLUMN movie_keyword.kind IS '種類(movie, tv, other)';
COMMENT ON COLUMN movie_keyword.keywords IS 'keywords(title, aks, genres, year, director, starts, countries, description)';
COMMENT ON COLUMN movie_keyword.j_tsv is '結巴的tsvector';

CREATE INDEX movie_keyword_idx_keyword
  ON movie_keyword
  USING gin
  (keywords COLLATE pg_catalog."default" gin_trgm_ops);

CREATE INDEX movie_keyword_idx_source
  ON movie_keyword
  USING btree
  (source COLLATE pg_catalog."default");

CREATE INDEX movie_keyword_j_tsv
  ON movie_keyword
  USING gin
  (j_tsv);


-- 最新電影(bt天堂)

Drop table if exists movie_latest;
CREATE TABLE movie_latest
(
  imdbid varchar(9) NOT NULL,
  rdate varchar(20) NOT NULL, -- bt天堂更新日期, e.g. 2012/03/20
  CONSTRAINT pk_movie_latest PRIMARY KEY (imdbid)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE movie_latest
  OWNER TO postgres;

COMMENT ON COLUMN movie_latest.rdate IS 'bt天堂更新日期, e.g. 2012/03/20';


-- 儲存從imdb資料庫中取得的imdb資料

Drop table if exists movie_imdb;
CREATE TABLE movie_imdb
(
  imdbid character(9) NOT NULL,
  CONSTRAINT movie_imdb_pk PRIMARY KEY (imdbid)
);


-- 儲存錯誤的imdbid

Drop table if exists movie_err_imdb;
CREATE TABLE movie_err_imdb
(
  imdbid character(9) NOT NULL,
  count int default(0),
  CONSTRAINT movie_err_imdb_pk PRIMARY KEY (imdbid)
);


-- 統計資料

CREATE TABLE movie_statistics
(
  id uuid NOT NULL,
  movieid varchar(20) NOT NULL, -- same as Movie.id
  imdbid varchar(9),
  type character(1), -- d:download/v:view/p:play
  datetime timestamp without time zone,
  CONSTRAINT movie_statistics_pk PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE movie_statistics
  OWNER TO postgres;


COMMENT ON COLUMN movie_statistics.movieid IS 'same as Movie.id';
COMMENT ON COLUMN movie_statistics.type IS 'd:download/v:view/p:play';


CREATE INDEX movie_statistics_idx_imdbid
  ON movie_statistics
  USING btree
  (imdbid COLLATE pg_catalog."default");


-- bt天堂

Drop Table if exists bttt;
CREATE TABLE bttt
(
  id varchar(10) NOT NULL,
  title varchar(256) NOT NULL,
  imdbid varchar(9),
  info_url varchar(2048) NOT NULL, -- bt天堂資訊頁, http://www.bttiantang.com/subject/27151.html
  content_urls json, -- bt種子網址
  rdate varchar(20) NOT NULL, -- bt天堂更新日期, e.g. 2012/03/20
  udate timestamp without time zone,
  md5sum varchar(32) NOT NULL,
  CONSTRAINT pk_bttt PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE bttt
  OWNER TO postgres;
  
  
COMMENT ON COLUMN bttt.info_url IS 'bt天堂資訊頁, http://www.bttiantang.com/subject/27151.html';
COMMENT ON COLUMN bttt.content_urls IS 'bt種子網址';
COMMENT ON COLUMN bttt.rdate IS 'bt天堂更新日期, e.g. 2012/03/20';


CREATE INDEX bttt_idx_imdbid
  ON bttt
  USING btree
  (imdbid COLLATE pg_catalog."default");

CREATE INDEX bttt_idx_udate
  ON bttt
  USING btree
  (rdate DESC);


-- 連續劇(含動漫)
Drop table if exists drama;
Create table drama(
  id varchar(20) NOT NULL, -- kb_+kuboID
  source varchar(10) NOT NULL, -- 來源(kubo)
  title varchar(512) NOT NULL,
  akas varchar(256)[], -- 別名
  kind varchar(10), -- 種類(0/動畫,1/台劇,2/韓劇,3/日劇,4/陸劇,5/港劇,6/美劇,7/其他,8/布袋戲
  genres varchar(20)[], -- 類型(推理、恐怖...)
  posterurl varchar(2048), -- 封面網址
  stars varchar(128)[], -- 演員
  year integer,
  region varchar(64), -- 地區
  description text, -- 劇情
  url varchar(2048), -- metadata來源網址
  kbid varchar(20), -- 酷播id
  play_urls json, -- 影片網址
  update_eps int, -- 更新的集數
  total_eps int, -- 全部集數
  completed bool, -- 是否完結
  vcount integer DEFAULT 0, -- 查看的次數
  dcount integer DEFAULT 0, -- 下載的次數
  pcount integer DEFAULT 0, -- 播放的次數
  rdate varchar(20) NOT NULL, -- kubo更新時間
  udate timestamp without time zone, -- 更新時間
  md5sum varchar(32),
  total_count integer DEFAULT 0,
  CONSTRAINT "pk_drama" PRIMARY KEY (id)
);

Comment on Column drama.id is 'kb_+kuboID';
Comment on Column drama.source is '來源(kubo)';
Comment on Column drama.akas is '別名';
Comment on Column drama.kind is '種類(0/動畫,1/台劇,2/韓劇,3/日劇,4/陸劇,5/港劇,6/美劇,7/其他,8/布袋戲';
Comment on Column drama.genres is '類型(推理、恐怖...)';
Comment on Column drama.posterurl is '封面網址';
Comment on Column drama.stars is '演員';
Comment on Column drama.region is '地區';
Comment on Column drama.description is '劇情';
Comment on Column drama.url is 'metadata來源網址';
Comment on Column drama.kbid is '酷播id';
Comment on Column drama.play_urls is '影片網址';
Comment on Column drama.update_eps is '更新的集數';
Comment on Column drama.total_eps is '全部集數';
Comment on Column drama.completed is ' 是否完結';
Comment on Column drama.vcount is '查看的次數';
Comment on Column drama.dcount is '下載的次數';
Comment on Column drama.pcount is '播放的次數';
Comment on Column drama.rdate is 'kubo更新時間';
Comment on Column drama.udate is '更新時間';


-- drama_keyword

Drop Table if exists drama_keyword;
Create table drama_keyword
(
    id varchar(20) not null, -- 'same as drama.id';
    keywords text, -- keywords(title, akas, genres, stars, region, description)
    j_tsv tsvector, -- 結巴的tsvector
    Constraint "drama_keyword_pk" Primary Key ("id")
);

Comment on Column drama_keyword.id is 'same as drama.id';
Comment on Column drama_keyword.keywords is 'keywords(title, akas, genres, stars, region, description)';
Comment on Column drama_keyword.j_tsv is '結巴的tsvector';

Drop index if exists drama_keyword_idx_keyword;
Create Index drama_keyword_idx_keyword
  On drama_keyword
  Using gin
  (keywords gin_trgm_ops);

CREATE INDEX drama_keyword_j_tsv
  ON drama_keyword
  USING gin
  (j_tsv);


-- 統計

CREATE TABLE drama_statistics
(
  id uuid NOT NULL,
  dramaid varchar(20) NOT NULL, -- same as drama.id
  type character(1), -- d:download/v:view/p:play
  datetime timestamp without time zone,
  CONSTRAINT drama_statistics_pk PRIMARY KEY (id)
);

COMMENT ON COLUMN drama_statistics.dramaid IS 'same as drama.id';
COMMENT ON COLUMN drama_statistics.type IS 'd:download/v:view/p:play';
