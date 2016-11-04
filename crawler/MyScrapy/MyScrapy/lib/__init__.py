# -*- coding: utf-8 -*-


class IVideoResourceExtractor(object):
    """ 取得播放資源的網址

    """

    def get_video_resources(self, links):
        """

        :param links: kubo player links,
            ['http://www.123kubo.com/168player/youtube.php?TDhvcGl0Q0NuVWZLMzRsUUJQcWw3QW...']
        :return: VideoResources,
        {
            'youtube': [{
                'title': '娘家_ep1',
                'play_url': 'http://www.123kubo.com/168player/youtube.php?TDhvcGl0Q0NuVWZLMzRsUUJQcWw3QWNWUFNa...',
                'video_urls': ['https://www.youtube.com/watch?v=TvJO5hgbkPE']
            }]
                }
        """
        raise NotImplementedError


class VideoResource(dict):

    def __init__(self, **kwargs):
        dict.__init__(kwargs)

    def add_resource(self, resname):
        self[resname] = []

    def del_resource(self, resname):
        if resname in self:
            del self[resname]

    def is_empty_resource(self, resname):
        """ 檢查該 resource 是否 video_urls 為空

        :param resname:
        :return:
        """

        for ep in self[resname]:
            if ep['video_urls']:
                return False
        return True

    def add_ep(self, resname, title, play_url, video_urls):
        self[resname].append({
            'title': title,
            'play_url': play_url,
            'video_urls': video_urls
        })
