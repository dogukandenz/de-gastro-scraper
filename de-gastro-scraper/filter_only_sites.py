import pandas as pd

df = pd.read_csv("out/gastro_germany.csv")
df = df.dropna(subset=["Website"])   # sadece websitesi olanlar kalsın
df.to_csv("out/gastro_with_sites.csv", index=False)
print("Kalan site sayısı:", len(df))
