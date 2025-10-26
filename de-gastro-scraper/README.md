# DE Gastro Scraper

This project assembles a GDPR-aware dataset of German gastronomy venues (restaurants, cafés, bars) with:
- Business Name
- Owner Name (Inhaber/Geschäftsführer where available)
- E-mail
- Postal Code
- Town
- Source URL (Impressum or the page where the contact/name was found)

## Approach

1. **Discovery (Overpass / OpenStreetMap):** Query `amenity=restaurant|cafe|bar` in Germany to obtain a fresh nationwide list with names and address tags. When present, we capture `website` and `contact:email` directly from OSM.
2. **Enrichment (Website crawl):** For venues with a website, we fetch the homepage and likely Impressum page(s). From German "Impressum" we try to parse the owner/manager and a working email using robust regex patterns (e.g., `Inhaber`, `Geschäftsführer`, `Betreiber`, etc.).
3. **Compliance:** 
   - Respect robots.txt (`ROBOTSTXT_OBEY=True`) and apply a modest `DOWNLOAD_DELAY`.
   - Store a `Source URL` pointing to the public page where data was found (OSM or the website/Impressum).
   - No scraping of platforms whose ToS forbid it (e.g., Google Maps HTML). If you want search lookups, use a compliant search API.
4. **Deduplication:** Hash on normalized `(business_name, postal_code, website)`.
5. **Exports:** CSV (and optionally XLSX) saved to `out/`.
6. **Verification:** A helper script picks 50 random rows, checks for email presence/format, and creates a checklist for manual re-checking.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# (Optional) pip install openpyxl  # for Excel export
```

### 1) Seed from Overpass
Run:
```bash
scrapy crawl overpass_seed -s FEED_FORMAT=jl -s FEED_URI=out/seed.jl
```
Then transform the JSON Lines into a CSV with required columns:
```python
import pandas as pd, json
rows=[json.loads(l) for l in open('out/seed.jl')]
df=pd.DataFrame(rows)
out=df.rename(columns={
    'business_name':'Business Name',
    'postal_code':'Postal Code',
    'town':'Town',
    'source_url':'Source URL',
    'website':'Website',
    'email':'E-mail'
})[['Business Name','Postal Code','Town','Source URL','Website','E-mail']]
out.to_csv('out/gastro_de_sample.csv', index=False)
```
> Note: OSM already contains many `website` and `contact:email` tags. Those can be exported immediately; owner names often require visiting the Impressum.

### 2) Enrich owner & email via websites
```bash
scrapy crawl website_enricher -a seeds_csv=out/gastro_de_sample.csv
```
The final CSV/XLSX will appear in `out/`.

## Verification

Run:
```bash
python verify_sample.py out/gastro_de_sample.csv
```
This writes `out/verification_sample.csv` with 50 random rows for manual checking. Target accuracy ≥ 90% across those checks.

## Limitations

- Not every venue publishes an owner/manager name or direct email. In those cases, the row will be excluded by default export rules. You can relax that in `pipelines.py`.
- Cookie walls / JS-heavy sites can hide email/owner details; Selenium can be added for those domains if needed.
- Overpass rate limits apply; split by region or time-slice if needed.
- Always review target sites' robots.txt and terms before crawling.

## Scaling notes

- Run the Overpass query in regional batches (by federal state) and rotate among mirrored endpoints.
- Increase `CONCURRENT_REQUESTS` gradually and keep `DOWNLOAD_DELAY` conservative.
- Persist per-domain crawl budgets to avoid overloading small sites.
- Consider a search API (compliant) to resolve official domains when OSM `website` is missing.

## How I Ran It (TL;DR)

1) Seed per state (OSM/Overpass) → one `.jl` per state (16 total)
2) Merge seeds (`merge_seeds.py`) → `gastro_germany.csv`
3) Filter only sites (`filter_only_site.py`) → `gastro_with_sites.csv`
4) Enrich websites (`website_enriched.py`) → `enriched.csv` (email + owner)
5) Postprocess (`postprocess.py`) → `gastro_germany_clean.csv`

---

### Pipeline (single-line)
Overpass (16 states) ──► `.jl` files ──► `merge_seeds.py` ──► `merged.csv` ──► `filter_only_site.py` ──► `gastro_with_sites.csv` ──► `website_enriched.py` ──► `enriched.csv` ──► `postprocess.py` ──► `final_dataset.csv`
