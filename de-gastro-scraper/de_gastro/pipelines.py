import hashlib
import pandas as pd
from pathlib import Path
from scrapy.exceptions import DropItem

REQUIRED_FOR_EXPORT = ["business_name", "postal_code", "town", "source_url"]

class DedupePipeline:
    def __init__(self):
        self.seen = set()

    def _key(self, item):
        base = f"{(item.get('business_name') or '').strip().lower()}|{(item.get('postal_code') or '').strip()}|{(item.get('website') or '').strip().lower()}"
        return hashlib.md5(base.encode('utf-8')).hexdigest()

    def process_item(self, item, spider):
        k = self._key(item)
        if k in self.seen:
            raise DropItem("duplicate item")
        self.seen.add(k)
        return item

class RequiredFieldsPipeline:
    def process_item(self, item, spider):
        for f in REQUIRED_FOR_EXPORT:
            if not item.get(f):
                raise DropItem(f"missing required field {f}")
        return item

class ExportPipeline:
    def __init__(self):
        self.rows = []

    def process_item(self, item, spider):
        row = {
            "Business Name": item.get("business_name"),
            "Owner Name": item.get("owner_name"),
            "E-mail": item.get("email"),
            "Postal Code": item.get("postal_code"),
            "Town": item.get("town"),
            "Source URL": item.get("source_url"),
        }
        self.rows.append(row)
        return item

    def close_spider(self, spider):
        outdir = Path(spider.custom_outdir or "out")
        outdir.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(self.rows)
        csv_path = outdir / "gastro_de_sample.csv"
        xlsx_path = outdir / "gastro_de_sample.xlsx"
        df.to_csv(csv_path, index=False)
        try:
            import openpyxl
            df.to_excel(xlsx_path, index=False)
        except Exception:
            pass  # Excel optional
