import re
from urllib.parse import urljoin

EMAIL_RE = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.I)
OWNER_HINTS = [r'Inhaber(?:in)?', r'Geschäftsführer(?:in)?', r'GF', r'Betreiber(?:in)?', r'Eigentümer(?:in)?', r'Verantwortlich(?:e|er)']

def extract_email(text):
    m = EMAIL_RE.search(text or '')
    return m.group(0) if m else None

def extract_owner_name(text):
    if not text: return None
    # Look for "Inhaber: Name" patterns
    for hint in OWNER_HINTS:
        m = re.search(hint + r'\s*[:\-]?\s*([A-ZÄÖÜ][^\n\r<]{2,80})', text, re.I)
        if m:
            name = m.group(1).strip()
            # stop at line break or double space or 'und' etc.
            name = re.split(r'(?:\s{2,}|\n|\r|,| und )', name)[0].strip()
            return name
    # Fallback: look for © Name or Impressum statements – too noisy; skip
    return None

def plausible_impressum_urls(base_url, html=''):
    cands = set()
    for kw in ['impressum', 'imprint', 'kontakt', 'kontakt/impressum']:
        cands.add(urljoin(base_url, '/' + kw.strip('/')))
    # Look for explicit links
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html or '', re.I):
        href = m.group(1)
        if any(k in href.lower() for k in ['impressum', 'imprint']):
            cands.add(urljoin(base_url, href))
    return list(cands)
