#!/usr/bin/env python3
"""
Asset Management Automation Script
从本地Excel读取数据并生成JSON
"""

import pandas as pd
import json
from datetime import datetime
import os

def sync_data():
    """从Excel同步数据并生成JSON"""
    print(f"🚀 开始同步数据 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 读取Excel文件
    excel_path = "/Users/kaijimima1234/Desktop/dashboard-demo/public/assets.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel文件不存在: {excel_path}")
        return False
    
    # 读取数据
    df_daily = pd.read_excel(excel_path, sheet_name='Daily')
    df_holdings = pd.read_excel(excel_path, sheet_name='Holdings')
    df_chart = pd.read_excel(excel_path, sheet_name='Chart')
    
    # 清理数据
    df_daily['date'] = pd.to_datetime(df_daily['date'], errors='coerce').astype(str)
    for col in ['cash_usd', 'gold_usd', 'stocks_usd', 'total_usd', 'nav']:
        df_daily[col] = pd.to_numeric(df_daily[col], errors='coerce').fillna(0).round(2)
    
    df_chart['date'] = pd.to_datetime(df_chart['date'], errors='coerce').astype(str)
    
    if 'timestamp' in df_holdings.columns:
        df_holdings['timestamp'] = df_holdings['timestamp'].astype(str)
    
    # 提取最新数据
    latest = df_daily.iloc[-1]
    
    # 生成JSON
    data = {
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "summary": {
            "total_usd": float(latest['total_usd']),
            "cash_usd": float(latest['cash_usd']),
            "gold_usd": float(latest['gold_usd']),
            "stocks_usd": float(latest['stocks_usd']),
            "nav": float(latest['nav']),
            "date": str(latest['date'])
        },
        "holdings": df_holdings.to_dict('records'),
        "chart_data": df_chart.to_dict('records'),
        "daily_data": df_daily.to_dict('records')
    }
    
    # 保存JSON
    output_path = "/tmp/Asset-Management/src/data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ data.json已更新")
    print(f"   总资产: ${data['summary']['total_usd']:,.2f}")
    print(f"   NAV: {data['summary']['nav']:.2f}")
    
    return True

if __name__ == "__main__":
    success = sync_data()
    if success:
        print("\n✅ 同步完成！")
    else:
        print("\n❌ 同步失败！")
        exit(1)
