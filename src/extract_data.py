import os
import json
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
import time
import subprocess
import re

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

def get_market_insights(holdings_summary):
    fallback = [
        {"type": "neutral", "asset": "Portfolio", "text": "数据已更新，建议关注市场波动。"},
        {"type": "opportunity", "asset": "Gold", "text": "黄金价格波动中，建议保持防御性仓位。"}
    ]
    try:
        prompt = f"Holdings: {holdings_summary}\nTask: 3 personalized insights in Chinese as a JSON list. IMPORTANT: Use English for the "type" field (warning, opportunity, neutral).. Fields: type, asset, text."
        raw_output = subprocess.check_output(["gemini", "--output-format", "json", prompt], text=True)
        data = json.loads(raw_output)
        inner_content = data.get('response', '')
        # Direct extraction of JSON list from markdown or raw text
        match = re.search(r'\[\s*\{.*\}\s*\]', inner_content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return fallback
    except:
        return fallback

def extract_data():
    try:
        if SERVICE_ACCOUNT_JSON:
            gc = gspread.authorize(Credentials.from_service_account_info(json.loads(SERVICE_ACCOUNT_JSON), scopes=['https://www.googleapis.com/auth/spreadsheets']))
        else:
            gc = gspread.service_account()
        
        sh = gc.open_by_key(SHEET_ID)
        ws_daily, ws_holdings = sh.worksheet("Daily"), sh.worksheet("Holdings")
        
        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        latest = df_daily.iloc[-1]
        
        df_holdings = get_as_dataframe(ws_holdings, evaluate_formulas=True).dropna(how='all', axis=0)
        df_holdings.columns = df_holdings.columns.astype(str).str.strip().str.lower()
        
        holdings = [{"symbol": str(r.get('symbol')), "name": str(r.get('name')), "qty": str(r.get('quantity')), "value": f"{safe_float(r.get('market_value_usd')):,.2f}"} for _, r in df_holdings.iterrows() if safe_float(r.get('market_value_usd')) > 0]

        insights = get_market_insights(f"Bal: {latest['total_usd']}, Assets: {holdings}")

        response = {
            "assets": [{"label": "Cash USD", "value": f"{safe_float(latest.get('cash_usd')):,.2f}"}, {"label": "Gold USD", "value": f"{safe_float(latest.get('gold_usd')):,.2f}"}, {"label": "US Stocks", "value": f"{safe_float(latest.get('stocks_usd')):,.2f}"}],
            "holdings": holdings, "total_balance": f"{safe_float(latest['total_usd']):,.2f}",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"), "insights": insights,
            "performance": {"1d": "Live", "summary": "Protocol v3.2 Ready"}
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__": extract_data()
