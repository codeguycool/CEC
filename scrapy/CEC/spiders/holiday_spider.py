# std lib
import os
import sys

# 3rd lib
import scrapy

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.normpath('%s/../' % CUR_PATH)))

# proj lib
import CEC.settings


class HolidaySpider(scrapy.Spider):
    name = 'holiday'
    allowed_domains = ['holiday.com.tw', 'youtube.com']
    start_urls = ['http://www.holiday.com.tw/song/Billboard.aspx?kind=jt']
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'ITEM_PIPELINES': {'CEC.pipelines.ktv_pipeline.KtvPipeline': 300}
    }

    def parse(self, response):
        songs = response.xpath("//table[@id='ctl00_ContentPlaceHolder1_dgSong']/tr[position()>1 and position() < last()]")
        lang_dict = {
            'c': 'M'
        }
        if songs:
            for song in songs:
                title = song.xpath('./td[5]/text()').extract()[0].strip()
                artist = song.xpath('./td[6]/a/text()').extract()[0].strip()
                lang = response.url[-1:]
                item = dict()
                item['title'] = title
                item['artist'] = artist
                item['lang'] = lang_dict.get(lang, lang)
                yield item

if __name__ == "__main__":
    # 3rd lib
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    # change pwd to project dir
    os.chdir(CEC.settings.DIR_PROJ)

    # run spider
    process = CrawlerProcess(get_project_settings())
    process.crawl(HolidaySpider)
    process.start()