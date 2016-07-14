-- local songs database

-- 歌曲清單

CREATE TABLE songs
(
  source varchar(20) NOT NULL, -- 來源(cashbox...)
  title varchar(256) NOT NULL, -- 歌名
  lang varchar(8), -- 語言, M:國語/E:英語/T:台語/C:粤語/J:日語/K:/韓語/THA:泰語
  artist varchar(128), -- 歌手
  keywords varchar(256), -- 將歌名及歌手轉小寫、繁體，將符號以空白取代，再用空白做分隔轉成list，用字母排序後再轉字串；例"心時代 畢書盡、陳勢安、陳彥允、李玉璽"變"心時代 畢書盡 陳勢安 陳彥允 李玉璽"
  vcount integer DEFAULT 0, -- 查看的次數
  dcount integer DEFAULT 0, -- 下載的次數
  pcount integer DEFAULT 0, -- 播放的次數
  total_count integer DEFAULT 0,
  keymd5 varchar(32) NOT NULL, -- 將keywords算md5
  udate timestamp without time zone, -- 更新時間
  CONSTRAINT songs_pk PRIMARY KEY (keymd5)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE songs
  OWNER TO postgres;


COMMENT ON COLUMN songs.source IS '來源(cashbox...)';
COMMENT ON COLUMN songs.title IS '歌名';
COMMENT ON COLUMN songs.lang IS '語言, M:國語/E:英語/T:台語/C:粤語/J:日語/K:/韓語/THA:泰語';
COMMENT ON COLUMN songs.artist IS '歌手';
COMMENT ON COLUMN songs.keywords IS '將歌名及歌手轉小寫、繁體，將符號以空白取代，再用空白做分隔轉成list，用字母排序後再轉字串；例"心時代 畢書盡、陳勢安、陳彥允、李玉璽"變"心時代 畢書盡 陳勢安 陳彥允 李玉璽"';
COMMENT ON COLUMN songs.vcount IS '查看的次數';
COMMENT ON COLUMN songs.dcount IS '下載的次數';
Comment ON COLUMN songs.pcount IS '播放的次數';
COMMENT ON COLUMN songs.keymd5 IS '將keywords算md5';
COMMENT ON COLUMN songs.udate IS '更新時間';


CREATE INDEX songs_idx_keymd5
  ON songs
  USING btree
  (keymd5 COLLATE pg_catalog."default");

CREATE INDEX songs_idx_lang
  ON songs
  USING btree
  (lang COLLATE pg_catalog."default");

CREATE INDEX songs_idx_udate
  ON songs
  USING btree
  (udate DESC);


-- 國語最新、台語最新...等清單

CREATE TABLE song_list
(
  source varchar(10) NOT NULL, -- 來源
  type character(1) NOT NULL, -- 類別, 1:新歌/2:點播排行/3:新歌排行
  lang varchar(8), -- 語言, M:國語/E:英語/T:台語/C:粤語/J:日語
  title varchar(256) NOT NULL, -- 歌名
  artist varchar(128), -- 歌手
  keymd5 varchar(32) NOT NULL, -- same as sonsgs.md5sum
  udate timestamp without time zone, -- 更新時間
  CONSTRAINT song_list_pk PRIMARY KEY (source, type, keymd5)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE song_list
  OWNER TO postgres;


COMMENT ON COLUMN song_list.source IS '來源';
COMMENT ON COLUMN song_list.type IS '類別, 1:新歌/2:點播排行/3:新歌排行';
COMMENT ON COLUMN song_list.lang IS '語言, M:國語/E:英語/T:台語/C:粤語/J:日語';
COMMENT ON COLUMN song_list.title IS '歌名';
COMMENT ON COLUMN song_list.artist IS '歌手';
COMMENT ON COLUMN song_list.keymd5 IS 'same as sonsgs.md5sum';
COMMENT ON COLUMN song_list.udate IS '更新時間';


-- 歌曲來源(Youtube)

Drop table if exists song_content;
CREATE TABLE song_content
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
  udate timestamp without time zone, -- 更新時間
  CONSTRAINT song_content_pk PRIMARY KEY (source, keymd5)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE song_content
  OWNER TO postgres;


COMMENT ON COLUMN song_content.source IS '來源(youtube, bt)';
COMMENT ON COLUMN song_content.fullname IS '來源歌曲全名';
COMMENT ON COLUMN song_content.poster_url IS '封面網址';
COMMENT ON COLUMN song_content.uploader IS '上傳者';
COMMENT ON COLUMN song_content.upload_date IS '上傳日期';
COMMENT ON COLUMN song_content.description IS '簡介';
COMMENT ON COLUMN song_content.duration IS '長度';
COMMENT ON COLUMN song_content.play_url IS '影片播放網址';
COMMENT ON COLUMN song_content.content IS '磁力連結或youtube的format資訊';
COMMENT ON COLUMN song_content.keymd5 IS 'same as sonsgs.md5sum';
COMMENT ON COLUMN song_content.md5sum IS 'content md5sum';
COMMENT ON COLUMN song_content.udate IS '更新時間';


CREATE INDEX song_content_idx_keymd5
  ON song_content
  USING btree
  (keymd5 COLLATE pg_catalog."default");

CREATE INDEX song_content_idx_udate
  ON song_content
  USING btree
  (udate DESC);


-- 統計資料

CREATE TABLE song_statistics
(
  id uuid NOT NULL,
  keymd5 varchar(32) NOT NULL, -- same as song.keymd5
  type character(1), -- d:download/v:view/p:play
  datetime timestamp without time zone,
  CONSTRAINT song_statistics_pk PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE song_statistics
  OWNER TO postgres;


COMMENT ON COLUMN song_statistics.keymd5 IS 'same as song.keymd5';
COMMENT ON COLUMN song_statistics.type IS 'd:download/v:view/p:play';
