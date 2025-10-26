import json, math
import scrapy
from urllib.parse import urlencode
from de_gastro.items import VenueItem

# Overpass endpoint
OVERPASS = "https://overpass-api.de/api/interpreter"

# amenity filters
TYPES = ["restaurant","cafe","bar"]

# Germany area id via area[name="Germany"];
QUERY_TMPL = '''
[out:json][timeout:60];
area["name"="Rheinland-Pfalz"][boundary=administrative]->.rp;
(
  node(area.rp)[amenity~"^(restaurant|cafe|bar)$"];
  way(area.rp)[amenity~"^(restaurant|cafe|bar)$"];
  relation(area.rp)[amenity~"^(restaurant|cafe|bar)$"];
);
out center tags;
'''
class OverpassSeedSpider(scrapy.Spider):
    name = "overpass_seed"
    custom_outdir = "out"

    def start_requests(self):
        data = QUERY_TMPL
        yield scrapy.FormRequest(
            OVERPASS,
            formdata={"data": data},
            method="POST",
            callback=self.parse_overpass
        )

    def parse_overpass(self, resp):
        j = json.loads(resp.text)
        for el in j.get("elements", []):
            tags = el.get("tags", {})
            if not tags: 
                continue
            name = tags.get("name") or tags.get("brand")
            if not name: 
                continue
            town = tags.get("addr:city") or tags.get("name:city") or tags.get("is_in:city")
            pc = tags.get("addr:postcode")
            website = tags.get("website") or tags.get("contact:website")
            email = tags.get("email") or tags.get("contact:email")
            item = VenueItem()
            item["business_name"] = name
            item["postal_code"] = pc
            item["town"] = town
            item["website"] = website
            item["email"] = email
            # initial source is OSM; source_url points to an OSM page
            osm_type = el.get("type")
            osm_id = el.get("id")
            item["source_url"] = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
            item["country"] = "DE"
            item["_source"] = "osm"
            yield item
