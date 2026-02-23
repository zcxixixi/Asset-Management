import pandas as pd
import json

XLSX_PATH = '/Users/kaijimima1234/Desktop/dashboard-demo/public/assets.xlsx'
OUTPUT_PATH = '/Users/kaijimima1234/Desktop/dashboard-demo/src/data.json'

def extract_data():
    try:
        # Load the Summary tab for top-level KPIs
        df_summary = pd.read_excel(XLSX_PATH, sheet_name='Summary', header=None)
        
        # Summary structure (from our earlier script knowledge):
        # D2: 7D Perf, D3: 30D Perf
        # We index using [row, col] -> D2 is row 1, col 3. D3 is row 2, col 3. (0-indexed)
        # Wait, let's use the Daily tab to be safe, it has all raw data.
        
        df_daily = pd.read_excel(XLSX_PATH, sheet_name='Daily')
        # Columns in Daily: Date, Total_USD, Cash, Stocks, Crypto, Gold, NAV
        # The latest row is usually the last one or we can just pick from df_daily
        
        # Let's clean the dataframe: dropna on Date
        df_daily = df_daily.dropna(subset=[df_daily.columns[0]])
        
        latest_row = df_daily.iloc[-1]
        
        # Calculate 7D and 30D from NAV locally if we don't look up Summary
        nav_series = df_daily.iloc[:, 6] # G column is NAV
        
        def safe_float(v):
            try: return float(str(v).replace(',', ''))
            except: return 1.0

        current_nav = safe_float(nav_series.iloc[-1])
        nav_7d_ago = safe_float(nav_series.iloc[-8]) if len(nav_series) >= 8 else safe_float(nav_series.iloc[0])
        nav_30d_ago = safe_float(nav_series.iloc[-31]) if len(nav_series) >= 31 else safe_float(nav_series.iloc[0])
        
        perf_7d = ((current_nav / nav_7d_ago) - 1) * 100
        response = {"assets": [], "chart_data": []}
        
        response["assets"] = [
            {"label": "Cash USD", "value": f"{safe_float(latest_row['cash_usd']):,.2f}"},
            {"label": "US Stocks", "value": f"{safe_float(latest_row['stocks_usd']):,.2f}"},
            {"label": "Gold USD", "value": f"{safe_float(latest_row['gold_usd']):,.2f}"},
        ]
        
        # Calculate performance
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
        
        response["total_balance"] = f"{safe_float(latest_row['total_usd']):,.2f}"
        
        # Chart Data (All available history)
        for _, row in df_daily.iterrows():
            dt = str(row['date']).split(' ')[0]
            val = safe_float(row['nav'])
            response["chart_data"].append({"date": dt, "value": val})
            
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(response, f, indent=2)
            
        print("Data successfully extracted to src/data.json")
    except Exception as e:
        print(f"Error extracting data: {e}")

if __name__ == "__main__":
    extract_data()
