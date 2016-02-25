# -*-coding: utf-8 -*-
'''Format of response contents.
'''

def c_movie(row, movie_content=None, detail=False):
    '''Movie content format.
    '''
    content = {
        'id': row.get('id', None),
        'source': row.get('source', None),
        'title': row.get('title', None),
        'poster': row.get('posterurl', None),
        'content': {
            'index': None,
            'play_link': None
        }
    }

    if row.get('imdbid', None): # patch content data if it has imdbid value.
        c_row = movie_content.get(row['imdbid'], None)
        if c_row:
            content['content'].update({
                'index': c_row.get('url', None),
                'play_link': c_row.get('link', None)
            })

    if detail:
        content.update({
            'directors': row.get('directors', []),
            'writers': row.get('writers', []),
            'stars': row.get('stars', []),
            'description': row.get('description', None)
        })

    return content

