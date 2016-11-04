-- local av database

-- trigram extension
Create extension if not exists pg_trgm;

-- av videos(metadata)

Drop Table if exists video;
Create Table video
(
    id varchar(32) not null, -- dmm品番
    title varchar(256) not null, --片名
    code varchar(32), -- 番號
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
    vcount integer DEFAULT 0, -- 查看的次數
    dcount integer DEFAULT 0, -- 下載的次數
    pcount integer DEFAULT 0, -- 播放的次數
    total_count integer DEFAULT 0,
    md5sum varchar(32) not null,
    udate timestamp, -- 更新時間
    constraint "video_pk" primary key(id)
);

Drop index if exists video_idx_udate;
Create Index video_idx_udate
  on video
  Using BTree
  (udate desc);

Comment on Column video.id is'dmm品番';
Comment on Column video.id is'番號';
Comment on Column video.title is'片名';
Comment on Column video.posterurl is'封面';
Comment on Column video.duration is'片長';
Comment on Column video.performer is'出演者';
Comment on Column video.category is'類別';
Comment on Column video.rating is'評分';
Comment on Column video.maker is'廠商';
Comment on Column video.series is'系列';
Comment on Column video.date is'商品発売日';
Comment on Column video.date2 is'配信開始日';
Comment on Column video.description is'簡介';
Comment on Column video.samples is'截圖';
Comment on Column video.url is'網址';
Comment ON COLUMN video.vcount IS '查看的次數';
Comment ON COLUMN video.dcount IS '下載的次數';
Comment ON COLUMN video.pcount IS '播放的次數';
Comment on Column video.udate is'更新時間';


-- video_keyword

Drop Table if exists video_keyword;
Create table video_keyword
(
    id varchar(32) not null, -- 'same as video.id';
    keywords text, -- keywords(id, title, performer, category, maker, series)
    Constraint "video_keyword_pk" Primary Key ("id")
);

Comment on Column video_keyword.id is'same as video.id';
Comment on Column video_keyword.keywords is'keywords(id, title, performer, category, maker, series)';

Drop index if exists video_keyword_idx_keyword;
Create Index video_keyword_idx_keyword
  On video_keyword
  Using gin
  (keywords gin_trgm_ops);


-- 統計資料

CREATE TABLE video_statistics
(
  id uuid NOT NULL,
  videoid varchar(32) NOT NULL, -- same as Video.id
  type character(1), -- d:download/v:view/p:play
  datetime timestamp without time zone,
  CONSTRAINT video_statistics_pk PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE video_statistics
  OWNER TO postgres;


COMMENT ON COLUMN video_statistics.videoid IS 'same as Video.id';
COMMENT ON COLUMN video_statistics.type IS 'd:download/v:view/p:play';