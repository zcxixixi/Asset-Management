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

def get_market_insights(summary):
    try:
        prompt = f"User Portfolio: {summary}\nTask: Provide 2 short investment insights in Chinese."
        result = subprocess.check_output(["gemini", "--output-format", "json", prompt], text=True)
        return json.loads(result)
    except: return ["数据已根据历史记录同步。", "建议保持资产配置稳定。"]

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
        ws_hist = sh.worksheet("Dashboard") 
        
        # 1. Pull Daily Data (Strict Source of Truth)
        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        latest_daily = df_daily.iloc[-1]
        latest_date = str(latest_daily['date']).split(' ')[0]
        
        # 2. Pull Holdings for that specific date
        df_hist = get_as_dataframe(ws_hist, evaluate_formulas=True).dropna(how='all', axis=0)
        df_hist.columns = df_hist.columns.astype(str).str.strip().str.lower()
        df_latest_holdings = df_hist[df_hist['date'].astype(str).str.contains(latest_date)]
        
        holdings_detail = []
        for _, row in df_latest_holdings.iterrows():
            holdings_detail.append({
                "symbol": str(row.get('symbol', 'N/A')),
                "name": str(row.get('name', 'N/A')),
                "qty": str(row.get('quantity', '0')),
                "price": f"{safe_float(row.get('price_usd', 0)):,.2f}",
                "value": f"{safe_float(row.get('market_value_usd', 0)):,.2f}",
                "account": str(row.get('account', 'N/A'))
            })
        
        # 3. Prepare categories from the Daily summary row
        asset_cards = [
            {"label": "Cash USD", "value": f"{safe_float(latest_daily.get('cash_usd', 0)):,.2f}"},
            {"label": "Gold USD", "value": f"{safe_float(latest_daily.get('gold_usd', 0)):,.2f}"},
            {"label": "US Stocks", "value": f"{safe_float(latest_daily.get('stocks_usd', 0)):,.2f}"}
        ]

        response = {
            "assets": asset_cards,
            "holdings": holdings_detail,
            "total_balance": f"{safe_float(latest_daily.get('total_usd', 0)):,.2f}",
            "performance": {
                "1d": f"{((safe_float(latest_daily.get('total_usd', 0)) / safe_float(df_daily.iloc[-2].get('total_usd', 1))) - 1) * 100:+.2f}%" if len(df_daily) > 1 else "0.00%",
                "summary": f"Recorded Snapshot: {latest_date}"
            },
            "chart_data": [{"date": str(r['date']).split(' ')[0], "value": safe_float(r['total_usd'])} for _, r in df_daily.iterrows()],
            "last_updated": latest_date,
            "insights": get_market_insights(f"Total: {latest_daily.get('total_usd', 0)}")
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        print(f"Sync Success: Strictly using recorded data for {latest_date}")
        
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        exit(1)

if __name__ == "__main__": extract_data()
