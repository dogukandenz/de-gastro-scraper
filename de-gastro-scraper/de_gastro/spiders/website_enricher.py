import scrapy
from urllib.parse import urlparse
from de_gastro.items import VenueItem
from de_gastro.utils.extractors import extract_email, extract_owner_name, plausible_impressum_urls

class WebsiteEnricherSpider(scrapy.Spider):
    name = "website_enricher"
    custom_outdir = "out"

    def __init__(self, seeds_csv="out/gastro_germany.csv", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seeds_csv = seeds_csv

    def start_requests(self):
        # Expect seeds CSV from overpass run; if none, skip
        import csv, os
        if not os.path.exists(self.seeds_csv):
            self.logger.error("Seeds CSV not found: %s", self.seeds_csv)
            return
        with open(self.seeds_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                website = row.get("Source URL")  # for OSM-only seeds we don't have website in CSV export; we revisit later
                # For enrichment, we actually want the website field – we will reconstruct using stored .jl in real run.
                # Here we just skip if we don't have one.
                site = row.get("Website") or ""
                if site and site.startswith("http"):
                    yield scrapy.Request(site, callback=self.parse_site, meta={"seed": row, "base": site}, dont_filter=True)

    def parse_site(self, resp):
        seed = resp.meta["seed"]
        base = resp.meta["base"]
        text = resp.text
        email = extract_email(text)
        owner = extract_owner_name(text)
        cand_urls = plausible_impressum_urls(base, text)

        if not (email and owner) and cand_urls:
            for u in cand_urls:
                yield scrapy.Request(u, callback=self.parse_impressum, meta={"seed": seed, "base": base}, dont_filter=True)
            return

        yield self._to_item(seed, resp.url, owner, email)

    def parse_impressum(self, resp):
        seed = resp.meta["seed"]
        text = resp.text
        owner = extract_owner_name(text)
        email = extract_email(text)
        yield self._to_item(seed, resp.url, owner, email)

    def _to_item(self, seed, src_url, owner, email):
        it = VenueItem()
        it["business_name"] = seed.get("Business Name") or seed.get("business_name")
        it["postal_code"] = seed.get("Postal Code") or seed.get("postal_code")
        it["town"] = seed.get("Town") or seed.get("town")
        it["owner_name"] = owner
        it["email"] = email
        it["source_url"] = src_url or seed.get("Source URL")
        it["_source"] = "site"
        return it
