import pandas as pd
import json
from datetime import datetime

print("🔄 立即同步数据...")

df = pd.read_excel("assets.xlsx", sheet_name="Daily")
df['date'] = pd.to_datetime(df['date']).astype(str)

data = {
    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "summary": {
        "total": float(df.iloc[-1]['total_usd']),
        "date": df.iloc[-1]['date']
    }
}

with open("src/data.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ 同步完成")
