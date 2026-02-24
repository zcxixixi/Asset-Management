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
    if pd.isna(v) or v is None:
        return 0.0
    try:
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v: return 0.0
            return float(v)
        return float(v)
    except:
        return 0.0

def get_market_insights(holdings_summary):
    print("Fetching market news and generating insights...")
    try:
        news_cmd = "curl -s 'https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml' | grep -oE '<title><!\[CDATA\[[^\]]+' | sed 's/<title><!\[CDATA\[//' | head -n 5"
        news_result = subprocess.check_output(news_cmd, shell=True, text=True)
        
        prompt = f"""
        User Portfolio: {holdings_summary}
        Latest Market News:
        {news_result}
        
        Task: Provide 2 short, professional investment insights (max 40 words each) in Chinese. 
        Focus on how the news might affect these specific holdings.
        Format: Return as a JSON list of strings.
        """
        gemini_cmd = ["gemini", "--output-format", "json", prompt]
        advice_result = subprocess.check_output(gemini_cmd, text=True)
        return json.loads(advice_result)
    except Exception as e:
        print(f"Warning: Insight generation failed: {e}")
        return ["市场数据波动中，建议保持当前观察。", "AI 投顾模块正在同步实时新闻源。"]

def extract_data(record_daily=False):
    try:
        if SERVICE_ACCOUNT_JSON:
            creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            gc = gspread.authorize(creds)
        else:
            gc = gspread.service_account()
        
        sh = gc.open_by_key(SHEET_ID)
        
        # 1. Fetch Daily sheet for history
        ws_daily = sh.worksheet("Daily")
        df_daily = get_as_dataframe(ws_daily, evaluate_formulas=True).dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        # 2. Fetch Real-time logic
        ws_logic = sh.worksheet("Hidden_Logic")
        logic_data = ws_logic.get_all_values()
        logic_dict = {row[3]: row[4] for row in logic_data if len(row) > 4}
        
        realtime_total = safe_float(logic_dict.get('Realtime_Total_USD', 0))
        
        # 3. Fetch current assets from Holdings
        ws_holdings = sh.worksheet("Holdings")
        df_holdings = get_as_dataframe(ws_holdings, evaluate_formulas=True).dropna(how='all', axis=0)
        df_holdings.columns = df_holdings.columns.astype(str).str.strip().str.lower()
        
        asset_cards = []
        holdings_detail = []
        asset_map = {} 
        
        for _, row in df_holdings.iterrows():
            label = str(row['name'])
            symbol = str(row['symbol'])
            qty = safe_float(row['quantity'])
            price = safe_float(row['price_usd'])
            mkt_val = safe_float(row['market_value_usd'])
            
            if mkt_val > 0:
                # For cards
                if label not in [a['label'] for a in asset_cards]:
                    asset_cards.append({"label": label, "value": f"{mkt_val:,.2f}"})
                
                # For detailed table
                holdings_detail.append({
                    "symbol": symbol,
                    "name": label,
                    "qty": qty,
                    "price": f"{price:,.2f}",
                    "value": f"{mkt_val:,.2f}",
                    "account": str(row['account'])
                })
                
                # Map for Daily record
                if 'cash' in label.lower() or '现金' in label: asset_map['cash'] = asset_map.get('cash', 0) + mkt_val
                elif 'gold' in symbol.lower() or 'gold' in label.lower(): asset_map['gold'] = asset_map.get('gold', 0) + mkt_val
                else: asset_map['stocks'] = asset_map.get('stocks', 0) + mkt_val

        # 4. Prepare Response
        today_str = time.strftime("%Y-%m-%d")
        response = {
            "assets": asset_cards,
            "holdings": holdings_detail,
            "total_balance": f"{realtime_total:,.2f}",
            "performance": {},
            "chart_data": [],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        
        # Chart Data
        for _, row in df_daily.iterrows():
            dt = str(row['date']).split(' ')[0]
            val = safe_float(row['total_usd'])
            if dt and dt != 'nan':
                response["chart_data"].append({"date": dt, "value": val})
        
        if response["chart_data"] and response["chart_data"][-1]["date"] == today_str:
            response["chart_data"][-1]["value"] = realtime_total
        else:
            response["chart_data"].append({"date": today_str, "value": realtime_total})

        # Performance
        last_recorded_total = safe_float(df_daily.iloc[-1]['total_usd'])
        perf_1d = ((realtime_total / last_recorded_total) - 1) * 100 if last_recorded_total > 0 else 0
        response["performance"] = {
            "1d": f"{perf_1d:+.2f}%",
            "summary": f"Market Data: {logic_dict.get('Last_Price_Sync', 'Real-time')}"
        }
        
        # 5. Insights
        holdings_summary = f"Total: {response['total_balance']}, Assets: {response['assets']}"
        response["insights"] = get_market_insights(holdings_summary)
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
            
        print(f"Extraction Success with Holdings Detail: {OUTPUT_PATH}")

        # 6. Optional: Record EOD Snapshot
        if record_daily:
            last_date_in_sheet = str(df_daily.iloc[-1]['date']).split(' ')[0]
            if last_date_in_sheet == today_str:
                print(f"Skipping record: {today_str} already exists.")
            else:
                last_nav = safe_float(df_daily.iloc[-1]['nav'])
                new_nav = last_nav * (realtime_total / last_recorded_total) if last_recorded_total > 0 else last_nav
                new_row = [
                    today_str,
                    round(asset_map.get('cash', 0), 2),
                    round(asset_map.get('gold', 0), 2),
                    round(asset_map.get('stocks', 0), 2),
                    round(realtime_total, 2),
                    round(new_nav, 3),
                    "EOD_AUTO_SNAPSHOT"
                ]
                ws_daily.append_row(new_row, value_input_option='USER_ENTERED')
                print(f"✅ EOD Snapshot recorded: {new_row}")
        
    except Exception as e:
        print(f"❌ Extraction Failed: {e}")
        exit(1)

if __name__ == "__main__":
    do_record = "--record" in sys.argv
    extract_data(record_daily=do_record)
