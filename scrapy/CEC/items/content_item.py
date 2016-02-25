import scrapy


class ContentItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    source = scrapy.Field()
    title = scrapy.Field()
    akas = scrapy.Field()
    year = scrapy.Field()
    imdbid = scrapy.Field()
    info_url = scrapy.Field()
    content_url = scrapy.Field()
    udate = scrapy.Field()
    md5sum = scrapy.Field()