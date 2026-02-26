import pandas as pd
import json
import os

df = pd.read_excel("assets.xlsx", sheet_name="Daily")
df['date'] = pd.to_datetime(df['date']).astype(str)
data = {"total": float(df.iloc[-1]['total_usd'])}
os.makedirs('src', exist_ok=True)
with open('src/data.json', 'w') as f:
    json.dump(data, f)
