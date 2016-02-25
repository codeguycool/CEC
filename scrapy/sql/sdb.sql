Drop extension if exists pg_trgm;
Create extension pg_trgm;

-- songs

Drop table if exists songs;
Create table songs
(
    id serial not null,
    title varchar(256) not null, -- 歌名
    lang varchar(8), -- 語言, M:國語語/E:英語/T:台語/C:粤語/J:日語/K:/韓語/THA:泰語
    artist varchar(128), -- 歌手
    gender char(1), --  性別, M: 男歌手/F:女歌手/G:團體或是合唱
    track varchar(2), -- 人聲軌，描述有人聲的 Audio track 在那一軌的資訊。 0/1/L:左聲道/R:右聲道/ST:立體聲
    ext varchar(8), -- 副檔名
    filename varchar(256) not null, -- KTV檔名
    magnet_link text, -- 磁力連結
    md5sum varchar(32),
    udate timestamp, -- 更新時間
    Constraint "songs_px" Primary Key ("id"),
    Constraint "songs_uq_filename" Unique ("filename")
);

Create Index songs_idx_lang
  On songs
  Using BTree
  (lang);

Comment on Column songs.title is'歌名';
Comment on Column songs.lang is'語言, M:國語/E:英語/T:台語/C:粤語/J:日語/K:/韓語/THA:泰語';
Comment on Column songs.artist is'歌手';
Comment on Column songs.gender is'性別, M:男歌手/F:女歌手/G:團體或是合唱';
Comment on Column songs.track is'人聲軌，描述有人聲的 Audio track 在那一軌的資訊。 0/1/L:左聲道/R:右聲道/ST:立體聲';
Comment on Column songs.ext is'副檔名';
Comment on Column songs.filename is'KTV檔名';
Comment on Column songs.magnet_link is'磁力連結';
Comment on Column songs.udate is'更新時間';


-- song_hot

Drop table if exists song_hot;
Create table song_hot
(
    song_id int not null
);