#!/usr/bin/env python3
"""
Local Asset Data Extraction Script
Reads directly from local assets.xlsx and updates data.json without Google APIs
"""
import os
import json
import pandas as pd
from datetime import datetime

INPUT_PATH = 'assets.xlsx'
OUTPUT_PATH = 'src/data.json'

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
        if not os.path.exists(INPUT_PATH):
            print(f"Error: {INPUT_PATH} not found in repository root.")
            return

        print("Reading local Excel file...")
        # Only Daily sheet exists locally
        df_daily = pd.read_excel(INPUT_PATH, sheet_name='Daily')
        df_daily = df_daily.dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        latest = df_daily.iloc[-1]
        
        # Local Excel doesn't have holdings, so we generate dynamic insights based off Daily
        insights = [
            {"type": "neutral", "asset": "Portfolio", "text": "Local synchronization active. Independent from Google services."}
        ]
        
        # Generate chart_data from Daily sheet historical NAV
        chart_data = []
        for _, row in df_daily.iterrows():
             dt = str(row['date']).split(' ')[0]
             val = safe_float(row['nav'])
             chart_data.append({"date": dt, "value": val})
        
        response = {
            "assets": [
                {"label": "Cash USD", "value": f"{safe_float(latest.get('cash_usd')):,.2f}"}, 
                {"label": "Gold USD", "value": f"{safe_float(latest.get('gold_usd')):,.2f}"}, 
                {"label": "US Stocks", "value": f"{safe_float(latest.get('stocks_usd')):,.2f}"}
            ],
            # Exposing basic properties correctly mapped for the dashboard UI
            "holdings": [], 
            "chart_data": chart_data,
            "total_balance": f"{safe_float(latest['total_usd']):,.2f}",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "insights": insights,
            "performance": {"1d": "Live", "summary": "Local File Protocol"}
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
            
        print(f"Success! Exported pristine data to {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"Error extracting data: {e}")

if __name__ == "__main__":
    extract_data()
