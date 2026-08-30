import scrapy


class ListingItem(scrapy.Item):
    """One handbag listing from a marketplace (filled in by spiders)."""

    marketplace = scrapy.Field()
    source_listing_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price_amount = scrapy.Field()
    currency = scrapy.Field()
    condition_raw = scrapy.Field()
    condition_normalized = scrapy.Field()
    attributes_raw = scrapy.Field()
    status = scrapy.Field()
    scraped_at = scrapy.Field()
    content_hash = scrapy.Field()
    product_variant_id = scrapy.Field()  # set by ProductLinkPipeline
    match_confidence = scrapy.Field()
    match_method = scrapy.Field()
    match_evidence = scrapy.Field()
    listing_id = scrapy.Field()  # set by PostgresListingPipeline
    _is_new_listing = scrapy.Field()  # set by PostgresListingPipeline
    image_url = scrapy.Field()
