import pandas as pd
import re
from urllib.parse import urlparse
from html import unescape

df = pd.read_csv("out/enriched.csv")

def norm_text(x: str):
    if not isinstance(x, str):
        return None
    x = x.replace("\u00a0", " ").replace("&nbsp;", " ")
    x = unescape(x)
    x = x.strip()
    # HTML tag kırp
    x = re.sub(r"<[^>]*>", " ", x)
    # quote/attribute kırıntıları
    x = re.sub(r'["\']\s*/?>$', "", x).strip()
    # çoklu boşluk
    x = re.sub(r"\s+", " ", x)
    return x or None

OWNER_BLACKLIST_SUBSTR = [
    "alt erstellt", "für die richtigkeit", "fuer die richtigkeit",
    "in eines tagesaktuellen", "figmeta", "fullscreen", "uexbl",
    "cookie", "stylesheet", "drittanbieter", "javascript", "script",
    "open-sans", "sans-serif", "font", "woff", "ttf", "css", "svg",
    "onclick", "data-layer", "tracking", "analytics",
    "der angegebenen e-mail-adresse sind", "angegebenen e-mail-adresse",
    "impressum", "kontakt", "privacy", "datenschutz", "agb", "terms", "policy",
    "http", "https", ".css", ".js", ".png", ".jpg", ".gif", ".woff"
]

OWNER_BLACKLIST_REGEX = [
    r'^[A-Za-z0-9+/=]{20,}$',   # base64 benzeri uzun blob
    r'[<>{}=\[\]]',            # html/attr karakterleri
]

def is_garbage_owner(s: str) -> bool:
    sl = s.lower()
    if any(tok in sl for tok in OWNER_BLACKLIST_SUBSTR):
        return True
    for rx in OWNER_BLACKLIST_REGEX:
        if re.search(rx, s):
            return True
    # çok noktalama/teknik karakter oranı (punctuation-heavy)
    punct_ratio = sum(ch in '"/\\<>={}[]|~`^;:' for ch in s) / max(1, len(s))
    if punct_ratio > 0.15:
        return True
    return False

def is_plausible_name(s: str) -> bool:
    # temel heuristikler
    if not (2 <= len(s) <= 60):
        return False
    if "@" in s:
        return False
    # en az 2 alfabetik karakter olsun
    if sum(ch.isalpha() for ch in s) < 2:
        return False
    # 6+ rakam içeriyorsa şüpheli
    if sum(ch.isdigit() for ch in s) >= 6:
        return False
    # 6+ kelimeyse büyük ihtimalle cümle/çöp
    if len(s.split()) > 6:
        return False
    return True

def clean_owner(x):
    x = norm_text(x)
    if not x:
        return None
    if is_garbage_owner(x):
        return None
    if not is_plausible_name(x):
        return None
    return x

df["owner_name"] = df.get("owner_name", pd.Series([None]*len(df))).apply(clean_owner)

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)
BAD_DOMAIN_SUBSTR = ["example", "beispiel", "domain.com", "localhost", "invalid", "test"]
GENERIC_LOCALS = {
    "info","kontakt","contact","mail","office","service","hello","hallo",
    "support","booking","reservierung","reservation","bestellung","shop",
    "sales","admin","webmaster","postmaster","noreply","no-reply","do-not-reply"
}

def normalize_email(raw):
    if not isinstance(raw, str):
        return None
    e = unescape(raw).replace("\u00a0", "").replace("&nbsp;", "").strip()
    e = re.sub(r'["<>]', '', e)
    e = re.sub(r"\s+", "", e)  # araya kaçan boşlukları sil
    return e or None

def clean_email(x):
    e = normalize_email(x)
    if not e:
        return None
    if "@" not in e:
        return None
    if not EMAIL_RE.match(e):
        return None
    el = e.lower()
    if any(b in el for b in BAD_DOMAIN_SUBSTR):
        return None
    if any(ext in el for ext in [".css",".js",".png",".jpg",".gif",".woff",".ttf"]):
        return None
    return e

df["email"] = df.get("email", pd.Series([None]*len(df))).apply(clean_email)


df["_email_is_generic"] = df["email"].apply(
    lambda e: isinstance(e, str) and e.split("@",1)[0].split("+",1)[0].lower() in GENERIC_LOCALS
)

def registrable_domain(url):
    try:
        netloc = urlparse(str(url)).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or None
    except:
        return None

if "website" in df.columns:
    df["_email_domain"] = df["email"].str.split("@").str[-1].str.lower()
    df["_site_domain"]  = df["website"].apply(registrable_domain)
    df["_email_matches_site"] = df.apply(
        lambda r: isinstance(r["_email_domain"], str) and isinstance(r["_site_domain"], str)
                  and (r["_email_domain"].endswith(r["_site_domain"]) or r["_site_domain"].endswith(r["_email_domain"])),
        axis=1
    )
else:
    df["_email_matches_site"] = None

df = df[df["email"].notna()]

keep_cols = [c for c in ["business_name","postal_code","town","email"] if c in df.columns]
if keep_cols:
    df = df.drop_duplicates(subset=keep_cols)

out_clean = "out/gastro_germany_clean.csv"
df.to_csv(out_clean, index=False, encoding="utf-8")
print("✅ Temiz CSV oluşturuldu:", out_clean)
print("Toplam temiz kayıt:", len(df))

sample_src = df.dropna(subset=["owner_name","email"]) if {"owner_name","email"}.issubset(df.columns) else pd.DataFrame()
if len(sample_src) >= 50:
    sample_src.sample(50, random_state=42).to_csv("out/verification_sample.csv", index=False, encoding="utf-8")
    print("✅ Verification sample kaydedildi: out/verification_sample.csv")
else:
    print(f"⚠️ 50 sample çıkacak kadar owner+email dolu kayıt yok! (Şu an: {len(sample_src)})")
