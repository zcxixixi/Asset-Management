import os
import json
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
import time
import subprocess

# --- CONFIGURATION ---
SHEET_ID = '1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE'
OUTPUT_PATH = 'src/data.json'
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

def get_market_insights(holdings_summary):
    """
    Fetch news and generate AI advice.
    """
    print("Fetching market news and generating insights...")
    try:
        # 1. Fetch some quick news via curl (using a simple RSS to text converter or similar)
        # For simplicity and reliability, we'll use a few top headlines from a finance API or RSS
        news_cmd = "curl -s 'https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml' | grep -oE '<title><!\[CDATA\[[^\]]+' | sed 's/<title><!\[CDATA\[//' | head -n 5"
        news_result = subprocess.check_output(news_cmd, shell=True, text=True)
        
        # 2. Construct prompt for Gemini
        prompt = f"""
        User Portfolio: {holdings_summary}
        Latest Market News:
        {news_result}
        
        Task: Provide 2 short, professional investment insights (max 40 words each) in Chinese. 
        Focus on how the news might affect these specific holdings (Cash, Gold, US Stocks).
        Format: Return as a JSON list of strings. 
        Example: ["建议对冲黄金波动...", "美股仓位建议保持..."]
        """
        
        # 3. Call Gemini
        gemini_cmd = ["gemini", "--output-format", "json", prompt]
        advice_result = subprocess.check_output(gemini_cmd, text=True)
        return json.loads(advice_result)
    except Exception as e:
        print(f"Warning: Insight generation failed: {e}")
        return ["市场数据波动中，建议保持当前观察。", "AI 投顾模块正在同步实时新闻源。"]

def validate_data(response, df_daily):
    print("Starting data validation...")
    required_keys = ["assets", "total_balance", "performance", "chart_data"]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing required key: {key}")
    
    latest_row = df_daily.iloc[-1]
    reported_total = safe_float(latest_row['total_usd'])
    summed_total = (safe_float(latest_row['cash_usd']) + 
                    safe_float(latest_row['gold_usd']) + 
                    safe_float(latest_row['stocks_usd']))
    
    if abs(reported_total - summed_total) > 1.0: # Relaxed slightly for legacy data rounding
        raise ValueError(f"Math Mismatch: Sum ({summed_total}) != Reported Total ({reported_total})")
    
    print("✅ Validation Passed.")

def extract_data():
    try:
        if SERVICE_ACCOUNT_JSON:
            creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
            gc = gspread.authorize(creds)
        else:
            gc = gspread.service_account()
        
        sh = gc.open_by_key(SHEET_ID)
        ws_daily = sh.worksheet("Daily")
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
            
        # VALIDATE
        validate_data(response, df_daily)
        
        # GENERATE INSIGHTS
        holdings_summary = f"Total: {response['total_balance']}, Assets: {response['assets']}"
        response["insights"] = get_market_insights(holdings_summary)
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
            
        print(f"Sync Success with Insights: {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        exit(1)

if __name__ == "__main__":
    extract_data()
