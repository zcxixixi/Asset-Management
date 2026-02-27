#!/usr/bin/env python3
"""
Real-Time Asset Synchronization Script
Uses yfinance to dynamically calculate the latest market values based on raw quantities listed in assets.xlsx
Supports the new Brokerage Export Format
"""
import os
import json
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime

INPUT_PATH = 'assets.xlsx'
OUTPUT_PATH = 'src/data.json'
REQUIRED_HOLDINGS_COLUMNS = {'symbol', 'name', 'quantity'}
REQUIRED_DAILY_COLUMNS = {'date', 'nav'}

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
        # Convert broker tickers like NVDA.US to Yahoo Finance friendly NVDA
        yf_symbol = symbol
        if str(symbol).endswith('.US'):
            yf_symbol = str(symbol).replace('.US', '')
        
        # Gold ETF vs Futures distinction
        if symbol == 'GOLD.CN' or 'GOLD' in str(symbol).upper():
            yf_symbol = 'GC=F'

        ticker = yf.Ticker(yf_symbol)
        fast_info = ticker.fast_info
        last_price = fast_info.get('last_price') if hasattr(fast_info, 'get') else fast_info['last_price']
        if last_price and last_price > 0:
            return float(last_price)
        history = ticker.history(period='5d')
        if not history.empty:
            return float(history['Close'].dropna().iloc[-1])
        raise ValueError(f"No valid market price for {yf_symbol}")
    except Exception as e:
        print(f"Warning: Failed to fetch {symbol} ({yf_symbol}): {e}")
        return 0.0

def format_asset_label(name, symbol):
    sym_upper = str(symbol).upper()
    if 'GOLD' in sym_upper or 'GC=F' in sym_upper: return 'Gold USD'
    if '.US' in sym_upper or sym_upper in ['NVDA', 'TSLA', 'QQQ', 'SGOV']: return 'US Stocks'
    if 'CASH' in sym_upper or sym_upper in ['USD', 'USDT']:
        return 'Cash USD'
    return name

def extract_data():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"{INPUT_PATH} not found in repository root")

    print("Reading local Excel Holdings (Broker Export Format)...")
    df_holdings = pd.read_excel(INPUT_PATH, sheet_name='Holdings')
    df_holdings = df_holdings.dropna(how='all')

    # Robustness: Normalize column names to lowercase and strip whitespace
    df_holdings.columns = [str(c).strip().lower() for c in df_holdings.columns]
    missing_holdings_columns = REQUIRED_HOLDINGS_COLUMNS - set(df_holdings.columns)
    if missing_holdings_columns:
        raise ValueError(f"Holdings sheet missing columns: {sorted(missing_holdings_columns)}")

    assets_grouped = {}
    total_balance = 0.0
    live_holdings = []

    print("\nFetching real-time market data via yfinance...")
    for _, row in df_holdings.iterrows():
        # Check if row is empty/NaN for symbol
        if pd.isna(row.get('symbol')): continue

        symbol = str(row.get('symbol', 'CASH')).strip()
        name = str(row.get('name', 'Unknown')).strip()
        qty = safe_float(row.get('quantity'))

        # Fetch Live Price & Compute Value
        price = get_realtime_price(symbol)
        usd_value = qty * price
        total_balance += usd_value

        print(f"[{symbol}] {qty} units @ ${price:,.2f} = ${usd_value:,.2f}")

        # Group into top-level dashboard categories (Cash, Gold, US Stocks)
        category_label = format_asset_label(name, symbol)
        if category_label not in assets_grouped:
            assets_grouped[category_label] = 0.0
        assets_grouped[category_label] += usd_value

        # Add to detailed holdings table if it's not pure cash and has value
        if symbol.upper() not in ('CASH', 'USD') and usd_value > 0:
            live_holdings.append({
                "symbol": symbol,
                "name": name,
                "qty": str(qty) if qty != int(qty) else str(int(qty)),
                "value": f"{usd_value:,.2f}"
            })

    # Format top level categories into correct array format for React UI
    final_assets = [
        {"label": "Cash USD", "value": f"{assets_grouped.get('Cash USD', assets_grouped.get('USD Cash', assets_grouped.get('现金', 0))):,.2f}"},
        {"label": "Gold USD", "value": f"{assets_grouped.get('Gold USD', 0):,.2f}"},
        {"label": "US Stocks", "value": f"{assets_grouped.get('US Stocks', 0):,.2f}"}
    ]

    # Read historical NAV for charts
    df_daily = pd.read_excel(INPUT_PATH, sheet_name='Daily')
    df_daily = df_daily.dropna(how='all', axis=1).dropna(how='all', axis=0)
    df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
    missing_daily_columns = REQUIRED_DAILY_COLUMNS - set(df_daily.columns)
    if missing_daily_columns:
        raise ValueError(f"Daily sheet missing columns: {sorted(missing_daily_columns)}")

    # Calculate trailing performance from nav records
    nav_series = df_daily['nav'].apply(safe_float)
    nav_series = nav_series.dropna()
    if nav_series.empty:
        raise ValueError("Daily.nav has no usable values")
    current_nav = nav_series.iloc[-1]
    nav_7d_ago = nav_series.iloc[-8] if len(nav_series) >= 8 else nav_series.iloc[0]
    perf_7d = ((current_nav / nav_7d_ago) - 1) * 100 if nav_7d_ago > 0 else 0

    chart_data = [{"date": str(row['date']).split(' ')[0], "value": safe_float(row['nav'])} for _, row in df_daily.iterrows()]
    if not chart_data:
        raise ValueError("chart_data generated empty from Daily sheet")

    # Generate dynamically aware insights based on our pipeline
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
        "performance": {"1d": "Live", "summary": "Broker Export Integration"}
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(response, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Pushed live calculated data to {OUTPUT_PATH}. Total NAV: ${total_balance:,.2f}")
    return response

if __name__ == "__main__":
    try:
        extract_data()
    except Exception as e:
        print(f"Error orchestrating pipeline: {e}", file=sys.stderr)
        raise
