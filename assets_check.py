import pandas as pd
import json
import sys

try:
    df = pd.read_excel("assets.xlsx", sheet_name="Daily")
    df['date'] = pd.to_datetime(df['date']).astype(str)
    data = {
        "last_updated": str(df.iloc[-1]['date']),
        "total": float(df.iloc[-1]['total_usd'])
    }
    with open("src/data.json", "w") as f:
        json.dump(data, f)
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
