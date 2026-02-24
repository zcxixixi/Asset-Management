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

def get_market_insights(holdings_summary):
    print("Fetching market news and generating insights...")
    try:
        news_cmd = "curl -s 'https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml' | grep -oE '<title><!\[CDATA\[[^\]]+' | sed 's/<title><!\[CDATA\[//' | head -n 5"
        news_result = subprocess.check_output(news_cmd, shell=True, text=True)
        prompt = f"Portfolio: {holdings_summary}\nNews: {news_result}\nTask: 2 short insights in Chinese (JSON list)."
        gemini_cmd = ["gemini", "--output-format", "json", prompt]
        advice_result = subprocess.check_output(gemini_cmd, text=True)
        return json.loads(advice_result)
    except: return ["市场数据同步中。", "建议关注持仓动态。"]

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
        ws_logic = sh.worksheet("Hidden_Logic")
        ws_history = sh.worksheet("Dashboard") 
        
        logic_data = ws_logic.get_all_values()
        logic_dict = {row[3]: row[4] for row in logic_data if len(row) > 4}
        realtime_total = safe_float(logic_dict.get('Realtime_Total_USD', 0))
        
        df_holdings = get_as_dataframe(ws_holdings, evaluate_formulas=True).dropna(how='all', axis=0)
        df_holdings.columns = df_holdings.columns.astype(str).str.strip().str.lower()
        
        asset_cards, holdings_detail, asset_map = [], [], {}
        today_str = time.strftime("%Y-%m-%d")
        
        for _, row in df_holdings.iterrows():
            name, symbol, qty, price, mkt_val = str(row['name']), str(row['symbol']), safe_float(row['quantity']), safe_float(row['price_usd']), safe_float(row['market_value_usd'])
            if mkt_val > 0:
                holdings_detail.append({"symbol": symbol, "name": name, "qty": qty, "price": f"{price:,.2f}", "value": f"{mkt_val:,.2f}", "account": str(row['account'])})
                if name not in [a['label'] for a in asset_cards]: asset_cards.append({"label": name, "value": f"{mkt_val:,.2f}"})
                if 'cash' in name.lower() or '现金' in name: asset_map['cash'] = asset_map.get('cash', 0) + mkt_val
                elif 'gold' in symbol.lower() or 'gold' in name.lower(): asset_map['gold'] = asset_map.get('gold', 0) + mkt_val
                else: asset_map['stocks'] = asset_map.get('stocks', 0) + mkt_val

        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        response = {
            "assets": asset_cards, "holdings": holdings_detail, "total_balance": f"{realtime_total:,.2f}",
            "performance": {"1d": f"{((realtime_total / safe_float(df_daily.iloc[-1]['total_usd'])) - 1) * 100:+.2f}%", "summary": "Guardian Sync Active"},
            "chart_data": [{"date": str(r['date']).split(' ')[0], "value": safe_float(r['total_usd'])} for _, r in df_daily.iterrows()],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        response["insights"] = get_market_insights(f"Total: {response['total_balance']}")
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f: json.dump(response, f, indent=2, ensure_ascii=False)
        print(f"Extraction Success.")

        if record_daily:
            if str(df_daily.iloc[-1]['date']).split(' ')[0] != today_str:
                new_daily_row = [today_str, round(asset_map.get('cash', 0), 2), round(asset_map.get('gold', 0), 2), round(asset_map.get('stocks', 0), 2), round(realtime_total, 2), round(safe_float(df_daily.iloc[-1]['nav']) * (realtime_total / safe_float(df_daily.iloc[-1]['total_usd'])), 3), "AUTO"]
                ws_daily.append_row(new_daily_row, value_input_option='USER_ENTERED')
            hist_rows = [[today_str, str(r['account']), str(r['symbol']), str(r['name']), safe_float(r['quantity']), safe_float(r['price_usd']), safe_float(r['market_value_usd'])] for _, r in df_holdings.iterrows()]
            ws_history.append_rows(hist_rows, value_input_option='USER_ENTERED')
            print(f"✅ Sync complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__": extract_data(record_daily=("--record" in sys.argv))
