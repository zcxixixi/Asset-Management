#!/usr/bin/env python3
"""
Real-Time Asset Synchronization Script
Uses yfinance to dynamically calculate the latest market values based on raw quantities listed in assets.xlsx
"""
import os
import json
import pandas as pd
import yfinance as yf
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

def get_realtime_price(symbol):
    if symbol.upper() == 'CASH': return 1.0
    try:
        return yf.Ticker(symbol).fast_info['last_price']
    except Exception as e:
        print(f"Warning: Failed to fetch {symbol}: {e}")
        return 0.0

def format_asset_label(name, symbol):
    if symbol == 'GC=F': return 'Gold USD'
    if symbol == 'NVDA' or symbol == 'TSLA': return 'US Stocks'
    return name

def extract_data():
    try:
        if not os.path.exists(INPUT_PATH):
            print(f"Error: {INPUT_PATH} not found in repository root.")
            return

        print("Reading local Excel Holdings...")
        # Read the new Holdings sheet
        df_holdings = pd.read_excel(INPUT_PATH, sheet_name='Holdings')
        df_holdings = df_holdings.dropna(how='all')
        
        assets_grouped = {}
        total_balance = 0.0
        live_holdings = []
        
        print("\nFetching real-time market data via yfinance...")
        for _, row in df_holdings.iterrows():
            symbol = str(row['Symbol']).strip()
            name = str(row['Name']).strip()
            qty = safe_float(row['Quantity'])
            
            # Fetch Live Price & Compute Value
            price = get_realtime_price(symbol)
            usd_value = qty * price
            total_balance += usd_value
            
            print(f"[{symbol}] {qty} units @ ${price:,.2f} = ${usd_value:,.2f}")
            
            # Group into the specific top-level dashboard categories (Cash, Gold, US Stocks)
            category_label = format_asset_label(name, symbol)
            if category_label not in assets_grouped:
                assets_grouped[category_label] = 0.0
            assets_grouped[category_label] += usd_value
            
            # Add to detailed holdings table if it's not pure cash and has value
            if symbol != 'CASH' and usd_value > 0:
                live_holdings.append({
                    "symbol": symbol,
                    "name": name,
                    "qty": str(qty) if qty != int(qty) else str(int(qty)),
                    "value": f"{usd_value:,.2f}"
                })

        # Format top level categories into correct array format for React UI
        final_assets = [
            {"label": "Cash USD", "value": f"{assets_grouped.get('Cash USD', assets_grouped.get('USD Cash', 0)):,.2f}"},
            {"label": "Gold USD", "value": f"{assets_grouped.get('Gold USD', 0):,.2f}"},
            {"label": "US Stocks", "value": f"{assets_grouped.get('US Stocks', 0):,.2f}"}
        ]

        # Read historical NAV for charts
        df_daily = pd.read_excel(INPUT_PATH, sheet_name='Daily')
        df_daily = df_daily.dropna(how='all', axis=1).dropna(how='all', axis=0)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        # Calculate trailing performance from nav records
        nav_series = df_daily['nav'].apply(safe_float)
        current_nav = nav_series.iloc[-1] if not nav_series.empty else 1.0
        nav_7d_ago = nav_series.iloc[-8] if len(nav_series) >= 8 else nav_series.iloc[0]
        perf_7d = ((current_nav / nav_7d_ago) - 1) * 100 if nav_7d_ago > 0 else 0
        
        chart_data = [{"date": str(row['date']).split(' ')[0], "value": safe_float(row['nav'])} for _, row in df_daily.iterrows()]

        # Generate dynamically aware insights based on our new pipeline super powers
        insights = [
            {"type": "opportunity", "asset": "NVIDIA Corp", "text": "Real-time AI ticker updates successfully firing via local yfinance engine."},
            {"type": "neutral", "asset": "Portfolio", "text": f"7-Day tracking NAV shift stands at {perf_7d:+.2f}%."}
        ]

        response = {
            "assets": final_assets,
            "holdings": live_holdings,
            "chart_data": chart_data,
            "total_balance": f"{total_balance:,.2f}",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "insights": insights,
            "performance": {"1d": "Live", "summary": "Full Auto yfinance Integration"}
        }

        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Pushed live calculated data to {OUTPUT_PATH}. Total NAV: ${total_balance:,.2f}")
        
    except Exception as e:
        print(f"Error orchestrating pipeline: {e}")

if __name__ == "__main__":
    extract_data()
