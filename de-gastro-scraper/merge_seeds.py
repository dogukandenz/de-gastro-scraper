import pandas as pd, json, glob

all_rows = []

# Bütün .jl dosyalarını oku
for file in glob.glob("out/seed_*.jl"):
    print("İşleniyor:", file)
    with open(file, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]
        all_rows.extend(rows)

df = pd.DataFrame(all_rows)

# Kolonları normalize et
df = df.rename(columns={
    'business_name':'Business Name',
    'addr:postcode':'Postal Code',
    'postal_code':'Postal Code',
    'addr:city':'Town',
    'town':'Town',
    'country':'Country',
    'source_url':'Source URL',
    'website':'Website',
    'email':'E-mail'
})

# Eksik kolonları ekle (varsa boş kalsın)
for col in ["Business Name","Postal Code","Town","State","Country","Source URL","Website","E-mail"]:
    if col not in df.columns:
        df[col] = None

# Kolon sırasını ayarla
df = df[["Business Name","Postal Code","Town","State","Country","Source URL","Website","E-mail"]]

# Kaydet
df.to_csv("out/gastro_germany.csv", index=False, encoding="utf-8")
print("Toplam kayıt:", len(df))
print("Kaydedildi: out/gastro_germany.csv")
