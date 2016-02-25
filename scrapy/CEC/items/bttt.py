import scrapy


class BtTTItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    akas = scrapy.Field()
    udate = scrapy.Field()
    imdbid = scrapy.Field()
    info_url = scrapy.Field()
    content_urls = scrapy.Field()