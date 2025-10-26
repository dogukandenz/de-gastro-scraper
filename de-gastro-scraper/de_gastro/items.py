import scrapy

class VenueItem(scrapy.Item):
    business_name = scrapy.Field()
    owner_name = scrapy.Field()
    email = scrapy.Field()
    postal_code = scrapy.Field()
    town = scrapy.Field()
    source_url = scrapy.Field()
    website = scrapy.Field()
    country = scrapy.Field()
    raw_impressum_url = scrapy.Field()
    # internal fields
    _source = scrapy.Field()  # 'osm' | 'site'
