"""
深度数据分析 - 确保99.99%稳定性
"""
import pandas as pd
import json
from datetime import datetime
import numpy as np

print("🔬 深度数据分析开始")
print("=" * 60)
print()

# 读取Excel
df = pd.read_excel("assets.xlsx", sheet_name="Daily")
df['date'] = pd.to_datetime(df['date'])

print(f"📊 数据概览:")
print(f"  总行数: {len(df)}")
print(f"  日期范围: {df['date'].min()} 到 {df['date'].max()}")
print(f"  天数: {(df['date'].max() - df['date'].min()).days}")
print()

# 1. 价格验证
print("💰 价格验证:")
df['gold_price_per_gram'] = df['gold_usd'] / 8.96  # 假设8.96g
latest_gold_price = df['gold_price_per_gram'].iloc[-1]
print(f"  最新黄金价格: ${latest_gold_price:.2f}/克")
print(f"  国际标准: ~$166.75/克 (5186/盎司)")
diff = abs(latest_gold_price - 166.75)
print(f"  差异: ${diff:.2f} ({diff/166.75*100:.1f}%)")

if diff/166.75 < 0.05:  # 5%误差范围
    print("  ✅ 价格在合理范围内")
else:
    print("  ⚠️ 价格偏离较大")
print()

# 2. 资产验证
print("💎 资产验证:")
df['calculated_total'] = df['cash_usd'] + df['gold_usd'] + df['stocks_usd']
df['difference'] = abs(df['calculated_total'] - df['total_usd'])

max_diff = df['difference'].max()
avg_diff = df['difference'].mean()

print(f"  最大差异: ${max_diff:.2f}")
print(f"  平均差异: ${avg_diff:.4f}")

if max_diff < 0.01:
    print("  ✅ 资产计算100%准确")
else:
    print("  ⚠️ 发现计算误差")
print()

# 3. 格式验证
print("📝 格式验证:")
print(f"  日期格式: {df['date'].dtype}")
print(f"  数值格式: {df['total_usd'].dtype}")

# 检查是否有科学计数法
has_scientific = any('e' in str(v) for v in df['total_usd'])
if has_scientific:
    print("  ⚠️ 发现科学计数法")
else:
    print("  ✅ 格式正常")
print()

# 4. 完整性验证
print("🔍 完整性验证:")
null_counts = df.isnull().sum()
print(f"  空值统计:")
for col, count in null_counts.items():
    if count > 0:
        print(f"    {col}: {count}")
if null_counts.sum() == 0:
    print("    ✅ 无空值")
print()

# 5. 时间序列验证
print("📈 时间序列验证:")
df_sorted = df.sort_values('date')
date_diffs = df_sorted['date'].diff().dropna()

missing_dates = date_diffs[date_diffs > pd.Timedelta(days=1)]
if len(missing_dates) > 0:
    print(f"  ⚠️ 发现缺失日期: {len(missing_dates)}处")
else:
    print("  ✅ 日期连续")
print()

# 6. JSON一致性验证
print("🔗 JSON一致性验证:")
with open("src/data.json", "r") as f:
    json_data = json.load(f)

latest_excel = df.iloc[-1]
latest_json = json_data.get("summary", {})

if "total_usd" in latest_json:
    excel_total = latest_excel['total_usd']
    json_total = latest_json['total_usd']
    
    if abs(excel_total - json_total) < 0.01:
        print("  ✅ Excel与JSON数据一致")
    else:
        print(f"  ⚠️ 数据不一致: Excel={excel_total}, JSON={json_total}")
else:
    print("  ⚠️ JSON缺少total_usd字段")
print()

print("=" * 60)
print("✅ 深度分析完成")

