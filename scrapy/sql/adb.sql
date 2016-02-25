Drop extension if exists pg_trgm;
Create extension pg_trgm;

-- video

Drop Table if exists video;
Create Table video(
    id varchar(20) not null, -- dmm品番
    title varchar(256) not null, --片名
    posterurl varchar(2048), -- 封面
    duration integer, -- 片長
    performer varchar(64), -- 出演者
    category varchar(128)[], -- 類別
    rating real, -- 評分
    maker varchar(32), -- 廠商
    series varchar(128), -- 系列
    date timestamp, -- 發片日期
    description text, -- 簡介
    samples varchar(2048)[], -- 截圖
    url varchar(2048) not null, -- 網址
    md5sum varchar(32) not null,
    udate timestamp, -- 更新時間
    constraint "video_pk" primary key(id)
);

Comment on Column video.id is'dmm品番';
Comment on Column video.title is'片名';
Comment on Column video.posterurl is'封面';
Comment on Column video.duration is'片長';
Comment on Column video.performer is'出演者';
Comment on Column video.category is'類別';
Comment on Column video.rating is'評分';
Comment on Column video.maker is'廠商';
Comment on Column video.series is'系列';
Comment on Column video.date is'發片日期';
Comment on Column video.description is'簡介';
Comment on Column video.samples is'截圖';
Comment on Column video.url is'網址';
Comment on Column video.udate is'更新時間';


-- video_keyword

Drop Table if exists video_keyword;
Create table video_keyword(
    id varchar(20) not null, -- 'same as video.id';
    keywords text, -- keywords(id, title, performer, category, maker, series)
    Constraint "video_keyword_pk" Primary Key ("id")
);

Comment on Column video_keyword.id is'same as video.id';
Comment on Column video_keyword.keywords is'keywords(id, title, performer, category, maker, series)';

Create Index video_keyword_idx_keyword
  On video_keyword
  Using gin
  (keywords gin_trgm_ops);
