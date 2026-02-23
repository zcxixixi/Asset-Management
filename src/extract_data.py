import os
import json
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
import time

# --- CONFIGURATION ---
SHEET_ID = '1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE'
OUTPUT_PATH = 'src/data.json'
# We'll allow loading from env var for GitHub Actions, or local file for dev
SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT') 

def safe_float(v):
    if pd.isna(v) or v is None:
        return 0.0
    try:
        if isinstance(v, str):
            return float(v.replace(',', '').replace('$', '').strip())
        return float(v)
    except:
        return 0.0

def validate_data(response, df_daily):
    """
    Robustness check: If any check fails, raise an exception to stop the sync.
    This prevents corrupted data from reaching the UI.
    """
    print("Starting data validation...")
    
    # 1. Schema Check
    required_keys = ["assets", "total_balance", "performance", "chart_data"]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing required key: {key}")
    
    # 2. Content Check
    if not response["assets"] or not response["chart_data"]:
        raise ValueError("Assets or Chart Data is empty.")
    
    # 3. Math Integrity Check
    latest_row = df_daily.iloc[-1]
    reported_total = safe_float(latest_row['total_usd'])
    summed_total = (safe_float(latest_row['cash_usd']) + 
                    safe_float(latest_row['gold_usd']) + 
                    safe_float(latest_row['stocks_usd']))
    
    # Margin of error for rounding (0.1 USD)
    if abs(reported_total - summed_total) > 0.1:
        raise ValueError(f"Math Mismatch: Sum ({summed_total}) != Reported Total ({reported_total})")
    
    # 4. NAV / Growth Check
    latest_nav = safe_float(latest_row['nav'])
    if latest_nav <= 0:
        raise ValueError(f"Invalid NAV: {latest_nav}")

    # 5. Timeline Check
    last_date = str(response["chart_data"][-1]["date"])
    if len(last_date) != 10 or "-" not in last_date:
        raise ValueError(f"Invalid Date Format: {last_date}")

    print("✅ Validation Passed: Data is consistent and accurate.")

def extract_data():
    try:
        # --- AUTHENTICATION ---
        if SERVICE_ACCOUNT_JSON:
            # GitHub Action mode (reading from env string)
            print("Authenticating via Service Account Secret...")
            creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
            gc = gspread.authorize(creds)
        else:
            # Local dev mode (using gog login or ~/.config/gspread/service_account.json)
            print("Authenticating via local credentials...")
            gc = gspread.service_account()
        
        sh = gc.open_by_key(SHEET_ID)
        ws_daily = sh.worksheet("Daily")
        
        # --- EXTRACTION ---
        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        latest_row = df_daily.iloc[-1]
        
        response = {
            "assets": [
                {"label": "Cash USD", "value": f"{safe_float(latest_row['cash_usd']):,.2f}"},
                {"label": "Gold USD", "value": f"{safe_float(latest_row['gold_usd']):,.2f}"},
                {"label": "US Stocks", "value": f"{safe_float(latest_row['stocks_usd']):,.2f}"},
            ],
            "total_balance": f"{safe_float(latest_row['total_usd']):,.2f}",
            "performance": {},
            "chart_data": [],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        
        # Calculate performance
        nav_series = df_daily['nav']
        current_nav = safe_float(nav_series.iloc[-1])
        nav_7d_ago = safe_float(nav_series.iloc[-8]) if len(nav_series) >= 8 else safe_float(nav_series.iloc[0])
        nav_30d_ago = safe_float(nav_series.iloc[-31]) if len(nav_series) >= 31 else safe_float(nav_series.iloc[0])
        
        perf_7d = ((current_nav / nav_7d_ago) - 1) * 100 if nav_7d_ago != 0 else 0
        perf_30d = ((current_nav / nav_30d_ago) - 1) * 100 if nav_30d_ago != 0 else 0

        response["performance"] = {
            "7d": f"{perf_7d:+.2f}%", 
            "30d": f"{perf_30d:+.2f}%", 
        }
        
        for _, row in df_daily.iterrows():
            dt = str(row['date']).split(' ')[0]
            val = safe_float(row['nav'])
            if dt and dt != 'nan':
                response["chart_data"].append({"date": dt, "value": val})
            
        # --- VALIDATION ---
        validate_data(response, df_daily)
        
        # --- OUTPUT ---
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
            
        print(f"Sync Success: {OUTPUT_PATH} updated.")
        
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        exit(1) # Critical failure for GitHub Actions to report

if __name__ == "__main__":
    extract_data()
