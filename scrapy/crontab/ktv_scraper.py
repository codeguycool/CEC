# -*- encoding: utf-8 -*-

""" 分析KTV檔名取出歌手、性別、歌名、語言、人聲軌等資訊，並建立KTV資料庫。

    install
    =======
    sudo pip install bencode
    sudo pip insstall psycopg2

"""

# std lib
import base64
import datetime
import hashlib
import json
import os
import re
import traceback
import urllib

# 3rd lib
import bencode
import psycopg2


DB_HOST = 'localhost'
DB_NAME = 'sdb'
PATH_KTV = '/Volumes/Karaoke/mandtaiwan'
PATH_TORRENT = '/Users/Lex/Downloads/torrent'

PATTERN_KTV = '([^\[]*)?(\[.*\])?[^\[]*_([^\[]*)(\[[^\]]*\])?[^\[]*(\[[^\]]*\])?[^\[]*(?:\[Karaoke\])?[^\[]*\.(.*)'
""" 歌手[性別]_歌名[語言][人聲軌][Karaoke].副檔名

    1. ([^\[]*)? 歌手
    2. (\[[M|F|G]\])? 性別
    3. [^\[]* 雜訊（若有則可過濾掉，不會塞進有用的資訊裡）
    4. _([^\[]*) 歌名
    5. (\[[^\]]*\])? 語言
    6. [^\[]* 雜訊（若有則可過濾掉，不會塞進有用的資訊裡）
    7. (\[[^\]]*\])? 人聲軌
    8. [^\[]* 雜訊（若有則可過濾掉，不會塞進有用的資訊裡）
    9. (?:\[Karaoke\])? Karoake
    10. [^\[]* 雜訊（若有則可過濾掉，不會塞進有用的資訊裡）
    11. \.(.*) 副檔名
"""


def get_ktvlist_by_dir():
    """ 從目錄中取出ktv檔案清單

    :return:
    """
    # FixMe: 如果有含子目錄的話，需要修改。
    return os.listdir(PATH_KTV)


def get_ktvlist_by_txt():
    """ 從整理好的歌單中取出ktv檔案清單

    目前是測試用，正式應該是透過目錄取得檔案清單

    :return:
    """
    # FixMe: 如果歌單格式有變，記得修改。
    from songdb import songsdb
    return [os.path.basename(song['path']) for song in songsdb]


def get_md5(filepath):
    """ 計算ktv檔案的md5

    :param filepath:
    :return:
    """
    fobj = open(filepath, mode='rb')
    md5 = hashlib.md5()

    while True:
        data = fobj.read(8192)
        if data:
            md5.update(data)
        else:
            break

    return md5.hexdigest()


def get_magnetlink(filepath):
    """ 透過torrent檔，取得磁力連結

    :param filepath:
    :return:
    """
    torrent = open(filepath, mode='r').read()
    metadata = bencode.bdecode(torrent)
    hashcontents = bencode.bencode(metadata['info'])
    digest = hashlib.sha1(hashcontents).digest()
    b32hash = base64.b32encode(digest)
    xt = 'urn:btih:%s' % b32hash
    dn = urllib.quote(metadata['info']['name'])
    # 加入track
    tr = '&tr='.join(urllib.quote_plus(tk[0]) for tk in metadata['announce-list']) if 'announce-list' in metadata else ''
    magneturi = 'magnet:?xt=%s&dn=%s%s' % (xt, dn, tr)
    return magneturi


def get_song_info(filename):
    """ 分析檔名，取得歌曲的資訊。

    :param filename: ktv檔名
    :return:
    """
    song_info = dict()
    song_info['artist'] = None
    song_info['gender'] = None
    song_info['title'] = None
    song_info['lang'] = None
    song_info['track'] = None
    song_info['ext'] = None
    song_info['magnet_link'] = None
    song_info['md5sum'] = None
    song_info['filename'] = filename
    song_info['udate'] = datetime.datetime.now()

    # 有'_'符號則用正規表示法處理
    if filename.find('_') > -1:
        result = re.match(PATTERN_KTV, filename, re.IGNORECASE)
        if result and result.re.groups == 6:
            song_info['artist'] = result.group(1) if result.group(1) else None
            song_info['gender'] = result.group(2).upper() if result.group(2) else None
            song_info['title'] = result.group(3) if result.group(3) else None
            song_info['lang'] = result.group(4).upper() if result.group(4) else None
            song_info['track'] = result.group(5).upper() if result.group(5) else None
            song_info['ext'] = result.group(6).upper() if result.group(6) else None
        else:
            return
    # 將檔名當做歌名來處理
    else:
        tokens = os.path.splitext(filename)
        song_info['title'] = tokens[0]
        song_info['ext'] = tokens[1][1:].upper()

    # todo: 如果有需要利用檔案來算md5的話
    # ktv_filepath = '%s/%s' % (PATH_KTV, filename)
    # if os.path.exists(ktv_filepath):
    #     song_info['md5sum'] = get_md5(ktv_filepath)

    # 如果有torrent檔的話，產生磁力連結
    torrent_filepath = '%s/%s.torrent' % (PATH_TORRENT, filename)
    if os.path.exists(torrent_filepath):
        song_info['magnet_link'] = get_magnetlink(torrent_filepath)

    return song_info


def normalize_song_value(song):
    """ 正規化資料，將lang, track, gender的括號去除，並把lang轉代號

    :param song:
    :return:
    """
    song['lang'] = song['lang'].replace('[', '').replace(']', '') if song['lang'] else song['lang']
    song['track'] = song['track'].replace('[', '').replace(']', '') if song['track'] else song['track']
    song['gender'] = song['gender'].replace('[', '').replace(']', '') if song['gender'] else song['gender']

    lang_dict = {
        '國': 'M',
        '国': 'M',
        '粵': 'C',
        '台': 'T',
        '闽': 'T',
        '英': 'E',
        '日': 'J',
        '韓': 'K',
        '韩': 'K',
        '泰': 'THA'
    }
    song['lang'] = lang_dict.get(song['lang'], song['lang'])


def is_value_validate(song):
    """ 檢查資料的值是不是都在合理範圍

    :param song:
    :return: bool
    """
    # FixMe: 如果有新的規則，記得修改
    gender_list = ['M', 'F', 'G', None]
    lang_list = ['M', 'C', 'T', 'E', 'J', 'K', 'THA', None]
    track_list = ['0', '1', 'L', 'R', 'ST', None]
    # 檢查性別
    if song['gender'] not in gender_list:
        return False
    # 檢查語言
    if song['lang'] not in lang_list:
        return False
    # 檢查人聲軌
    if song['track'] not in track_list:
        return False
    # 歌名與副檔名不可為空
    if song['ext'] is None or song['title'] is None:
        return False

    return True


def insert_db(song):
    """ 將KTV存入DB

    :param song:
    :return:
    """
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user='postgres')
        cursor = conn.cursor()
        # 沒有存在相同檔名才insert
        cursor.execute("""
        Insert into songs(title, lang, artist, gender, track, ext, filename, magnet_link, md5sum)
        Select %(title)s, %(lang)s, %(artist)s, %(gender)s, %(track)s, %(ext)s, %(filename)s, %(magnet_link)s,
        %(md5sum)s
        Where Not Exists (Select id from songs where filename=%(filename)s)
        """, song)
        conn.commit()
    except:
        print traceback.format_exc()
    finally:
        cursor.close()
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    # 取得KTV清單
    # todo: 如果要更改取得清單的方式，記得更改
    files = get_ktvlist_by_txt()
    # 測試資料
    # files = []
    # files += [
    #     # Karaoke
    #     '劉錫明[M]_愛已落空[M][R][Karaoke].MPG',
    #     '劉錫明[M]_愛已落空[M][R][KARAOKE].MPG',
    #     # 歌名
    #     '_愛已落空[M].MPG',
    #     '_愛已落空.MPG',
    #     '愛已落空.mpg',
    #     # 歌手名
    #     '夢飛船+陶晶瑩[G]_愛 喲[M][L].mpg',
    #     '夢飛船&陶晶瑩[G]_愛 喲[M][L].mpg',
    #     # 語言
    #     '劉錫明[M]_愛已落空[國][R].MPG',
    #     # 人聲軌
    #     '劉錫明[M]_愛已落空[國][ST].MPG',
    #     # 雜訊
    #     '劉錫明[M]雜訊_愛已落空[M][0][KARAOKE].MPG',
    #     '劉錫明[M]_愛已落空[M]雜訊[0][KARAOKE].MPG',
    #     '劉錫明[M]_愛已落空[M][0]雜訊[KARAOKE].MPG',
    #     '劉錫明[M]_愛已落空[M][0][KARAOKE]雜訊.MPG',
    # ]

    # Parse KTV 檔名失敗
    list_parse_error = []
    # 不合法的值
    list_invalidate = []

    for fname in files:
        # 取得KTV相關資訊
        song = get_song_info(fname)

        # 無法取得KTV相關資訊
        if song is None:
            list_parse_error.append(fname)
            continue

        # 正規化
        normalize_song_value(song)

        # KTV的相關資訊有不合法的值
        if not is_value_validate(song):
            list_invalidate.append(fname)
            continue

        # 存入資料庫
        insert_db(song)

        # 印出資訊，將udate、md5sum、magnet_link不重要的資訊移除
        song.pop('udate')
        song.pop('md5sum')
        song.pop('magnet_link')
        print '%s:\r\n %s' % (fname, json.dumps(song, ensure_ascii=False))

    # 印出Parse KTV 檔名失敗的清單
    if list_parse_error:
        print '\r\nParse KTV 檔名失敗:'
        for f in list_parse_error:
            print f

    # 印出有不合法值的清單
    if list_invalidate:
        print '\r\n有不合法的值:'
        for f in list_invalidate:
            print f