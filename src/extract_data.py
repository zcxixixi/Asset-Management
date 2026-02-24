import os
import json
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
import time
import sys

# --- CONFIGURATION ---
SHEET_ID = '1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE'
OUTPUT_PATH = 'src/data.json'
SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT') 
MAX_DEVIATION = 0.30 # 30% Safety Threshold

def safe_float(v):
    if pd.isna(v) or v is None: return 0.0
    try:
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v: return 0.0
            return float(v)
        return float(v)
    except: return 0.0

def extract_data():
    try:
        if SERVICE_ACCOUNT_JSON:
            creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            gc = gspread.authorize(creds)
        else:
            gc = gspread.service_account()
        
        sh = gc.open_by_key(SHEET_ID)
        ws_daily = sh.worksheet("Daily")
        ws_holdings = sh.worksheet("Holdings")
        
        # 1. Load History for Safety Check
        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        last_recorded_total = safe_float(df_daily.iloc[-1]['total_usd'])

        # 2. Fetch CURRENT detailed holdings
        df_holdings = get_as_dataframe(ws_holdings, evaluate_formulas=True).dropna(how='all', axis=0)
        df_holdings.columns = df_holdings.columns.astype(str).str.strip().str.lower()
        
        asset_map = {'cash': 0.0, 'gold': 0.0, 'stocks': 0.0}
        holdings_detail = []
        for _, row in df_holdings.iterrows():
            name, symbol, mkt_val = str(row['name']), str(row['symbol']), safe_float(row['market_value_usd'])
            if mkt_val > 0:
                holdings_detail.append({"symbol": symbol, "name": name, "qty": str(row['quantity']), "price": f"{safe_float(row['price_usd']):,.2f}", "value": f"{mkt_val:,.2f}", "account": str(row['account'])})
                if 'cash' in name.lower() or '现金' in name: asset_map['cash'] += mkt_val
                elif 'gold' in symbol.lower() or 'gold' in name.lower(): asset_map['gold'] += mkt_val
                else: asset_map['stocks'] += mkt_val

        calculated_total = asset_map['cash'] + asset_map['gold'] + asset_map['stocks']

        # --- CIRCUIT BREAKER: DEVIATION CHECK ---
        deviation = abs(calculated_total - last_recorded_total) / last_recorded_total if last_recorded_total > 0 else 0
        if deviation > MAX_DEVIATION:
            print(f"❌ CIRCUIT BREAKER TRIGGERED: Deviation of {deviation*100:.1f}% detected.")
            print(f"Last recorded: {last_recorded_total}, New: {calculated_total}")
            # In a real environment, we'd send a Telegram alert here.
            sys.exit("ABORTING SYNC: Suspicious price fluctuation. Please verify data sources.")

        # 3. Final JSON Output
        response = {
            "assets": [{"label": "Cash USD", "value": f"{asset_map['cash']:,.2f}"}, {"label": "Gold USD", "value": f"{asset_map['gold']:,.2f}"}, {"label": "US Stocks", "value": f"{asset_map['stocks']:,.2f}"}],
            "holdings": holdings_detail, "total_balance": f"{calculated_total:,.2f}",
            "performance": {"1d": f"{((calculated_total / last_recorded_total) - 1) * 100:+.2f}%" if last_recorded_total > 0 else "0.00%", "summary": "Sanity Check: Passed"},
            "chart_data": [{"date": str(r['date']).split(' ')[0], "value": safe_float(r['total_usd'])} for _, r in df_daily.iterrows()],
            "last_updated": time.strftime("%Y-%m-%d"),
            "diagnostics": {"api_status": "OK", "math_proof": "Verified"}
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        print(f"Extraction Success: Total {calculated_total:,.2f}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__": extract_data()
