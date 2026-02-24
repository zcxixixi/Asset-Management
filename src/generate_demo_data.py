import pandas as pd
import json
import random
import os

XLSX_PATH = '/Users/kaijimima1234/Desktop/dashboard-demo/public/assets.xlsx'
OUTPUT_PATH = '/Users/kaijimima1234/Desktop/dashboard-demo/src/data.json'

def generate_demo_data():
    try:
        df_daily = pd.read_excel(XLSX_PATH, sheet_name='Daily')
        df_daily = df_daily.dropna(subset=[df_daily.columns[0]])
        latest_row = df_daily.iloc[-1]
        
        def safe_float(v):
            try: return float(str(v).replace(',', ''))
            except: return 1.0

        # Scale down wealth further (1/10th of the previous 1/3 scale, so overall 1/30 scale)
        SCALAR = 0.0333

        response = {"assets": [], "chart_data": []}
        
        # Preserve existing insights from Planner Agent
        if os.path.exists(OUTPUT_PATH):
            try:
                with open(OUTPUT_PATH, 'r') as f:
                    existing = json.load(f)
                    if "insights" in existing:
                        response["insights"] = existing["insights"]
            except Exception:
                pass
                
        response["assets"] = [
            {"label": "Cash USD", "value": f"{(safe_float(latest_row['cash_usd']) * SCALAR):,.2f}"},
            {"label": "US Stocks", "value": f"{(safe_float(latest_row['stocks_usd']) * SCALAR):,.2f}"},
            {"label": "Gold USD", "value": f"{(safe_float(latest_row['gold_usd']) * SCALAR):,.2f}"},
        ]
        
        # Calculate performance metrics (performance is scale-invariant, so we can use real NAV curve)
        nav_series = df_daily['nav']
        current_nav = safe_float(nav_series.iloc[-1])
        nav_7d_ago = safe_float(nav_series.iloc[-8]) if len(nav_series) >= 8 else safe_float(nav_series.iloc[0])
        nav_30d_ago = safe_float(nav_series.iloc[-31]) if len(nav_series) >= 31 else safe_float(nav_series.iloc[0])
        
        perf_7d = ((current_nav / nav_7d_ago) - 1) * 100
        perf_30d = ((current_nav / nav_30d_ago) - 1) * 100

        response["performance"] = {
            "7d": f"{perf_7d:+.2f}%", 
            "30d": f"{perf_30d:+.2f}%", 
        }
        
        response["total_balance"] = f"{(safe_float(latest_row['total_usd']) * SCALAR):,.2f}"
        
        # Chart Data (All available history - applying scalar to NAV)
        for _, row in df_daily.iterrows():
            dt = str(row['date']).split(' ')[0]
            val = safe_float(row['nav']) * SCALAR
            response["chart_data"].append({"date": dt, "value": val})
            
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(response, f, indent=2)
            
        print(f"Demo data successfully generated to src/data.json using scalar {SCALAR}")
    except Exception as e:
        print(f"Error extracting data: {e}")

if __name__ == "__main__":
    generate_demo_data()
