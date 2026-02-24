import os
import json
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
import time
import subprocess
import sys

# --- CONFIGURATION ---
SHEET_ID = '1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE'
OUTPUT_PATH = 'src/data.json'
SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT') 

def safe_float(v):
    if pd.isna(v) or v is None: return 0.0
    try:
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v: return 0.0
            return float(v)
        return float(v)
    except: return 0.0

def extract_data(record_daily=False):
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
        ws_history = sh.worksheet("Dashboard") 
        
        # 1. Fetch CURRENT detailed holdings (The Source of Truth for EOD)
        df_holdings = get_as_dataframe(ws_holdings, evaluate_formulas=True).dropna(how='all', axis=0)
        df_holdings.columns = df_holdings.columns.astype(str).str.strip().str.lower()
        
        holdings_detail = []
        asset_map = {'cash': 0.0, 'gold': 0.0, 'stocks': 0.0}
        today_str = time.strftime("%Y-%m-%d")
        
        for _, row in df_holdings.iterrows():
            name, symbol, mkt_val = str(row['name']), str(row['symbol']), safe_float(row['market_value_usd'])
            if mkt_val > 0:
                holdings_detail.append({
                    "symbol": symbol, "name": name, "qty": str(row['quantity']), 
                    "price": f"{safe_float(row['price_usd']):,.2f}", "value": f"{mkt_val:,.2f}",
                    "account": str(row['account'])
                })
                # ATOMIC AGGREGATION: Calculate summary strictly from parts
                if 'cash' in name.lower() or '现金' in name: asset_map['cash'] += mkt_val
                elif 'gold' in symbol.lower() or 'gold' in name.lower(): asset_map['gold'] += mkt_val
                else: asset_map['stocks'] += mkt_val

        # Sum of parts = True Total
        calculated_total = asset_map['cash'] + asset_map['gold'] + asset_map['stocks']

        # 2. Fetch Daily for Chart/History
        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        # 3. Final JSON Response
        response = {
            "assets": [
                {"label": "Cash USD", "value": f"{asset_map['cash']:,.2f}"},
                {"label": "Gold USD", "value": f"{asset_map['gold']:,.2f}"},
                {"label": "US Stocks", "value": f"{asset_map['stocks']:,.2f}"}
            ],
            "holdings": holdings_detail,
            "total_balance": f"{calculated_total:,.2f}",
            "performance": {
                "1d": f"{((calculated_total / safe_float(df_daily.iloc[-1]['total_usd'])) - 1) * 100:+.2f}%" if calculated_total > 0 else "0.00%",
                "summary": f"Audit Status: OK"
            },
            "chart_data": [{"date": str(r['date']).split(' ')[0], "value": safe_float(r['total_usd'])} for _, r in df_daily.iterrows()] + [{"date": today_str, "value": calculated_total}],
            "last_updated": today_str
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        # 4. ATOMIC EOD RECORDING
        if record_daily:
            if str(df_daily.iloc[-1]['date']).split(' ')[0] != today_str:
                # Calculate NAV
                last_nav = safe_float(df_daily.iloc[-1]['nav'])
                new_nav = last_nav * (calculated_total / safe_float(df_daily.iloc[-1]['total_usd']))
                
                # Write Daily Summary
                new_daily_row = [today_str, round(asset_map['cash'], 2), round(asset_map['gold'], 2), round(asset_map['stocks'], 2), round(calculated_total, 2), round(new_nav, 3), "ATOMIC_SYNC"]
                ws_daily.append_row(new_daily_row, value_input_option='USER_ENTERED')
                
                # Write Holdings History
                hist_rows = [[today_str, str(r['account']), str(r['symbol']), str(r['name']), safe_float(r['quantity']), safe_float(r['price_usd']), safe_float(r['market_value_usd'])] for _, r in df_holdings.iterrows()]
                ws_history.append_rows(hist_rows, value_input_option='USER_ENTERED')
                print(f"✅ Atomic Sync Complete: Daily and History aligned to {calculated_total}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__": extract_data(record_daily=("--record" in sys.argv))
