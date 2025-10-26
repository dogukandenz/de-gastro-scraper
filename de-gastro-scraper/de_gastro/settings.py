BOT_NAME = "de_gastro"

SPIDER_MODULES = ["de_gastro.spiders"]
NEWSPIDER_MODULE = "de_gastro.spiders"

ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 8
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de,en-US;q=0.9,en;q=0.8',
    'User-Agent': 'de-gastro-scraper/1.0 (+research; contact: example@example.com)'
}

ITEM_PIPELINES = {
    "de_gastro.pipelines.DedupePipeline": 100,
    "de_gastro.pipelines.RequiredFieldsPipeline": 200,
    "de_gastro.pipelines.ExportPipeline": 800,
}

FEED_EXPORT_ENCODING = "utf-8"

LOG_LEVEL = "INFO"

FEED_EXPORT_FIELDS = [
    "business_name",
    "postal_code",
    "town",
    "state",
    "country",
    "website",
    "email",
    "owner_name",
    "source_url",
    "_source"
]