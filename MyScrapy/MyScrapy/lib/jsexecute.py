# -*- coding: utf-8 -*-

# std
import json

# 3rd
import js2py


class JsExecute(object):
    """ 執行 javascript，取出酷播 javascript 裡藏的 playdata

    """

    def get_playdata(self, html):
        """

        :param html:
        :return: playdata
            {
                "Vod": [
                    "僵 國語",
                    "港劇",
                    "/vod-show-id-65-p-1.html"
                ],
                "Data": [{
                    "servername": null,
                    "playname": "xigua",
                    "playurls": [
                        [
                            "殭国语01.mkv",
                            "ftp://a.gbl.114s.com:20320/4422/殭国语01.mkv",
                            "/vod-play-id-82698-sid-0-pid-1.html"
                        ],
                        [
                            "殭国语02.mkv",
                            "ftp://a.gbl.114s.com:20320/1525/殭国语02.mkv",
                            "/vod-play-id-82698-sid-0-pid-2.html"
                        ]
                    ]
                }, {
                    "servername": null,
                    "playname": "bj58",
                    "playurls": [
                        [
                            "殭國語01",
                            "fun58_756xPfUP%2FBnVcLgrsGABxA9JAVH7vs1Is2QVrFm2Xqo%3D",
                            "/vod-play-id-82698-sid-2-pid-1.html"
                        ],
                        [
                            "殭國語02(影像有問題介意者勿點)",
                            "fun58_k%2BC2MosJD0Zd1HxdnGkfy7PIhyuq2m9YY2OJWloA0BA%3D",
                            "/vod-play-id-82698-sid-2-pid-2.html"
                        ]
                    ]
                }]
            }

        """
        result = self.execute(html)
        playdata = json.loads(result)
        return playdata

    def execute(self, html):
        """ execute javascript 實作

        :param html:
        :return:
        """
        raise NotImplementedError


class Js2PyExecutor(JsExecute):
    """ 利用 Js2Py 實作

    """

    def execute(self, html):
        jsscript = Js2PyExecutor.get_jsscript(html)
        result = js2py.eval_js(jsscript)
        return result

    @classmethod
    def get_jsscript(cls, html):
        start = html.find("eval")
        end = html.find("</script>", start)
        return html[start:end]
