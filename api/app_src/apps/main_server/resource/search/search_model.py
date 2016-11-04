"""Model class
"""
# app module
from accessor.avs import search_avs, search_total as a_total, suggest_keyword as a_keyword
from accessor.tvs import search_tvs, search_total as t_total
from accessor.movies import search_movies, search_total as m_total, suggest_keyword as m_keyword
from accessor.karaokes import search_karaokes, search_total as k_total
from framework.err import ERR_REQUEST_ARG, RequestError
from framework.response import Response


class SearchModel:

    def _parse_args(self, url, params):
        """ Common arguments hanlder.

        [Arguments]
            url[0] : string.
                Search type.
            keyword : string.
                Search keyword.
            file_filter   : int string.
                File filter.
            keyword_filter  : string.
                Keyword filter.
            ordering  : int.
                Ordering rule.
            since  : int string.
                Response data start from.
            limit  : int string.
                Number of response rows to display.
            lang  : string.
                To choose display content.
        """
        # Get args
        args = {
            'media_type': url[0] if url else None,
            'keyword': params.get_string('keyword', u'').split(),
            'file_filter': params.get_int('file_filter', None),  # Not implement
            'keyword_filter': params.get_string('keyword_filter', u'').split(),
            'ordering': params.get_int('ordering', 0),
            'since': params.get_int('since', None),
            'limit': params.get_limit('limit', 10),
            'lang': params.get_string('lang', None)
        }

        # handle value
        if not args['keyword']:
            raise RequestError(ERR_REQUEST_ARG, str_data=('keyword not found'))

        return args

    def search_media(self, url, params, request, response):
        """ Search multimedia information.

        [Arguments]
            See _parse_args.
        """
        args = self._parse_args(url, params)

        ret = {
            'detail': True,  # FIXME if this filed is not a common data.
            'media_type': args['media_type']
        }

        try:
            search_inst = {
                'movies': search_movies,
                'karaokes': search_karaokes,
                'avs': search_avs,
                'tvs': search_tvs
            }[args.pop('media_type')]
        except:
            raise RequestError(ERR_REQUEST_ARG, str_data=('media type error'))

        search_ret = search_inst(**args)
        ret.update(search_ret)

        return Response(model_data=ret)

    def search_index(self, url, params, request, response):
        """ Search multimedia index.

        [Arguments]
            Take Args: keyword, lang.
            See _parse_args.

            range  : list of string.
                Search range.
        """
        args = self._parse_args(url, params)
        args['keyword'] = list(set(args['keyword']))

        inst_map = {
            'movies': m_total,
            'karaokes': k_total,
            'avs': a_total,
            'tvs': t_total
        }

        # additional args
        search_range = params.get_list('range', inst_map.keys())

        ret = {}
        for key in search_range:
            ret[key] = inst_map[key](args['keyword'], args['lang'])

        return Response(content=ret)

    def suggest_keyword(self, url, params, request, response):
        """ Suggest keyword.

        [Arguments]
            media_type : string.
                Media type.
            media_id   : string.
                Target media ID.
            lang       : string.
                To choose display content.
        """
        media_type = params.get_string('media_type', None)
        media_id = params.get_string('media_id', None)
        lang = params.get_string('lang', None)

        if not media_id or not media_type or not lang:
            raise RequestError(ERR_REQUEST_ARG, str_data=('args missing'))

        try:
            search_inst = {
                'movies': m_keyword,
                'avs': a_keyword
            }[media_type]
        except:
            raise RequestError(ERR_REQUEST_ARG, str_data=('media_type error'))

        return Response(content={'keywords': search_inst(media_id, lang)})
