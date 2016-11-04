# -*-coding: utf-8 -*-
"""Format of response contents.
"""


def c_movie(row, movie_content=None, detail=False):
    """Movie content format.
    """
    content = {
        'id': row.get('id', None),
        'imdb_id' : row.get('imdbid', None),
        'source': row.get('source', None),
        'source_url': row.get('url', None),
        'title': row.get('title', None),
        'alias' : row.get('akas', []),
        'rating' : row.get('rating', None),
        'content': []
    }
    
    # Display poster as possible 
    content['large_poster'] = row.get('posterurl', None)
    poster = row.get('thumbnailurl', None)
    content['poster'] = poster if poster else content['large_poster']

    if row.get('imdbid', None):  # patch content data if it has imdbid value.
        c_rows = movie_content.get(row['imdbid'], [])
        for c_row in c_rows:
            source = c_row.get('source', None)
            # tudou only show BT by SPEC.
            if source and source not in ['tudou']:
                content['content'].append({
                    'index': c_row.get('info_url', None),
                    'play_link': c_row.get('content_url', None),
                    'source': source
                })

    if detail:
        content.update({
            'countries': row.get('countries', []),
            'directors': row.get('directors', []),
            'genres': row.get('genres', []),
            'writers': row.get('writers', []),
            'stars': row.get('stars', []),
            'description': row.get('description', None)
        })

    return content


def c_karaoke(row, karaoke_content=None, detail=False):
    """Karaoke content format.
    """
    content = {
        'id': row.get('keymd5', None),
        'title': row.get('title', None),
        'artist': row.get('artist', None),
        'song_lang': row.get('lang', None),
        'poster': None,
        'content': []
    }

    if karaoke_content:
        c_rows = karaoke_content.get(row['keymd5'], [])
        for c_row in c_rows:  # FIXME: After SPEC is clear, we will re-write it.
            content_data = {  # for youtube.
                'source': c_row.get('source', None),
                'play_link': c_row.get('play_url', None),
                'name': c_row.get('fullname', None),
                'screenshot': c_row.get('poster_url', None),
                'resolution': sorted(
                    [k for k in c_row.get('content', {}).keys()],
                    key=lambda r: int(r),
                    reverse=True
                )
            }

            if detail:
                content_data.update({
                    'uploader': c_row.get('uploader', None),
                    'description': c_row.get('description', None),
                    'duration': c_row.get('duration', None)
                })

            content['content'].append(content_data)

            if not content['poster']:
                content['poster'] = content_data['screenshot']

    return content


def c_search_karaoke(row, detail=True):
    return c_karaoke(row=row, karaoke_content={row['keymd5']: [row]}, detail=detail)


def c_av(row, detail=False):
    """AV content format.
    """
    content = {
        'id': row.get('id', None),
        'title': row.get('title', None),
        'poster': row.get('posterurl', None),
        'performer': row.get('performer', []),
        'source_url': row.get('url', None)
    }

    if detail:
        content.update({
            'duration': row.get('duration', None),
            'categories': row.get('category', []),  # Return data key CAN NOT use 'category' FOR FE template code issue.
            'rating': row.get('rating', None),
            'maker': row.get('maker', None),
            'series': row.get('series', None),
            'description': row.get('description', None),
            'date': str(row['date']).split()[0] if row['date'] else None,
            'samples': row.get('samples', [])
        })

    return content


def c_tv(row, detail=False):
    """TV content format.
    """
    content = {
        'id': row.get('id', None),
        'source': row.get('source', None),
        'title': row.get('title', None),
        'alias': row.get('akas', []),
        'kind': row.get('kind', None),
        'genres': row.get('genres', []),
        'poster': row.get('posterurl', None), 
        'stars': row.get('stars', []),
        'year': row.get('year', None),
        'region': row.get('region', None),
        'description': row.get('description', None),
        'source_url': row.get('url', None),
        'update_eps': row.get('update_eps', None),
        'total_eps': row.get('total_eps', None),
        'completed': row.get('completed', False),
        'rdate': str(row['rdate']).split()[0] if row['rdate'] else None,
        'file_source': row.get('file_source', [])
    }

    # filter out resource not in SPEC.
    # Notice: Move this part in query sql if we need.
    if content['file_source']:
        content['file_source'] = [
            key for key in content['file_source'] if key not in ('youku', 'letv', 'sohu', 'iqiyi', 'tudou')
        ]

    if detail:
        content.update({
            'play_content': row.get('play_link', None)
        })

    return content
