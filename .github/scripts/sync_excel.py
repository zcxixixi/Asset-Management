import pandas as pd
import json
from datetime import datetime
import os

print("🚀 自动同步本地Excel数据")
print()

# 注意：这个脚本需要Excel文件能够从本地同步到GitHub
# 如果Excel文件在本地，需要通过其他方式同步（如手动上传、Git LFS等）

# 读取本地Excel文件
excel_path = "assets.xlsx"  # 假设Excel文件在仓库根目录

if not os.path.exists(excel_path):
    print("❌ Excel文件不存在，跳过同步")
    exit(0)

try:
    # 读取Excel数据
    df_daily = pd.read_excel(excel_path, sheet_name='Daily')
    df_holdings = pd.read_excel(excel_path, sheet_name='Holdings')
    df_chart = pd.read_excel(excel_path, sheet_name='Chart')
    
    # 清理数据
    df_daily['date'] = pd.to_datetime(df_daily['date'], errors='coerce')
    for col in ['cash_usd', 'gold_usd', 'stocks_usd', 'total_usd', 'nav']:
        df_daily[col] = pd.to_numeric(df_daily[col], errors='coerce').fillna(0).round(2)
    
    # 将所有日期列转换为字符串
    df_daily['date'] = df_daily['date'].astype(str)
    df_chart['date'] = pd.to_datetime(df_chart['date'], errors='coerce').astype(str)
    
    if 'timestamp' in df_holdings.columns:
        df_holdings['timestamp'] = df_holdings['timestamp'].astype(str)
    
    print(f"✅ Daily: {len(df_daily)} 行")
    print(f"✅ Holdings: {len(df_holdings)} 行")
    print(f"✅ Chart: {len(df_chart)} 行")
    print()
    
    # 提取最新数据
    latest_row = df_daily.iloc[-1]
    latest_date = df_daily['date'].iloc[-1]
    
    print(f"💰 最新数据 ({latest_date}):")
    print(f"   总资产: ${float(latest_row['total_usd']):,.2f}")
    print()
    
    # 生成JSON数据
    data = {
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "summary": {
            "total_usd": float(latest_row['total_usd']),
            "cash_usd": float(latest_row['cash_usd']),
            "gold_usd": float(latest_row['gold_usd']),
            "stocks_usd": float(latest_row['stocks_usd']),
            "nav": float(latest_row['nav']),
            "date": latest_date
        },
        "holdings": df_holdings.to_dict('records'),
        "chart_data": df_chart.to_dict('records'),
        "daily_data": df_daily.to_dict('records')
    }
    
    # 保存JSON文件
    os.makedirs('src', exist_ok=True)
    with open('src/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ data.json已生成")
    print()
    
except Exception as e:
    print(f"❌ 同步失败: {e}")
    import traceback
    traceback.print_exc()

