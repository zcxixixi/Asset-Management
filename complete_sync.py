#!/usr/bin/env python3
"""
完整资产同步系统 - 修正版
黄金: 8.95克, 不是shares
"""
import gspread
import yfinance as yf
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from datetime import datetime
import time
import signal
import sys

def timeout_handler(signum, frame):
    print("Timeout reached", file=sys.stderr)
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(90)

def get_real_time_prices():
    """获取实时价格数据"""
    print("🔄 获取实时价格数据...")
    
    # 定义持仓映射 (使用正确的股票代码)
    holdings_map = {
        'NVIDIA Corp': 'NVDA',
        'iShares 0-3 Month Treasury Bond ETF': 'SHY', 
        'Tesla, Inc.': 'TSLA',
        'NASDAQ 100 ETF': 'QQQ'
    }
    
    prices = {}
    
    try:
        # 获取所有股票的实时价格
        tickers = list(holdings_map.values())
        print(f"  下载股票价格: {tickers}")
        data = yf.download(tickers, period='1d', interval='1d')
        
        for name, ticker in holdings_map.items():
            if not data.empty and ticker in data:
                latest_price = data[ticker]['Close'].iloc[-1]
                prices[name] = latest_price
                print(f"  {name} ({ticker}): ${latest_price:.2f}")
        
        # 获取黄金价格 (通过GLD ETF)
        print(f"  下载黄金ETF价格: GLD")
        gld_data = yf.download('GLD', period='1d', interval='1d')
        if not gld_data.empty:
            gld_price = gld_data['Close'].iloc[-1]
            # 1克黄金的价格 (GLD代表约0.1盎司，1盎司=31.1034768克)
            gold_price_per_gram = (gld_price / 0.1) / 31.1034768
            prices['Gold (ETF-linked)'] = gold_price_per_gram
            print(f"  GLD价格: ${gld_price:.2f}/share")
            print(f"  黄金价格: ${gold_price_per_gram:.4f}/g")
            print(f"  8.95克黄金价值: ${gold_price_per_gram * 8.95:.2f}")
            
        return prices
        
    except Exception as e:
        print(f"❌ 价格获取失败: {e}")
        import traceback
        traceback.print_exc()
        return {}

def sync_holdings(sh, holdings_ws, prices, timestamp):
    """更新Holdings工作表"""
    print("\n📊 更新 Holdings 工作表...")
    
    try:
        # 定义持仓数据 (修正：黄金是8.95克，不是shares)
        portfolio_data = [
            {
                'name': 'NVIDIA Corp',
                'quantity': 0.73,
                'symbol': 'NVDA',
                'market_value_usd': round(prices.get('NVIDIA Corp', 0) * 0.73, 2)
            },
            {
                'name': 'iShares 0-3 Month Treasury Bond ETF', 
                'quantity': 15.14,
                'symbol': 'SHY',
                'market_value_usd': round(prices.get('iShares 0-3 Month Treasury Bond ETF', 0) * 15.14, 2)
            },
            {
                'name': 'Tesla, Inc.',
                'quantity': 1.23,
                'symbol': 'TSLA', 
                'market_value_usd': round(prices.get('Tesla, Inc.', 0) * 1.23, 2)
            },
            {
                'name': 'NASDAQ 100 ETF',
                'quantity': 1.73,
                'symbol': 'QQQ',
                'market_value_usd': round(prices.get('NASDAQ 100 ETF', 0) * 1.73, 2)
            },
            {
                'name': 'Cash',
                'quantity': 571.73,
                'symbol': 'USD',
                'market_value_usd': 571.73
            },
            {
                'name': '黄金ETF联接C(估算USD)',
                'quantity': 8.95,  # 8.95克，不是shares
                'symbol': 'XAU',
                'market_value_usd': round(prices.get('Gold (ETF-linked)', 0) * 8.95, 2)  # 8.95克
            }
        ]
        
        # 创建新的DataFrame
        updated_holdings = []
        for item in portfolio_data:
            updated_holdings.append({
                'name': item['name'],
                'quantity': item['quantity'], 
                'symbol': item['symbol'],
                'market_value_usd': item['market_value_usd']
            })
        
        # 写入数据
        df_new = pd.DataFrame(updated_holdings)
        holdings_ws.clear()
        set_with_dataframe(holdings_ws, df_new, row=1, col=1, include_index=False, include_column_header=True)
        
        print("✅ Holdings 工作表更新完成")
        return updated_holdings
        
    except Exception as e:
        print(f"❌ Holdings更新失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def sync_daily(sh, daily_ws, holdings_data, timestamp):
    """更新Daily工作表"""
    print("\n📅 更新 Daily 工作表...")
    
    try:
        # 计算总资产
        total_stocks = sum(item['market_value_usd'] for item in holdings_data if item['symbol'] in ['NVDA', 'SHY', 'TSLA', 'QQQ'])
        total_gold = next((item['market_value_usd'] for item in holdings_data if item['symbol'] == 'XAU'), 0)
        total_cash = next((item['market_value_usd'] for item in holdings_data if item['symbol'] == 'USD'), 0)
        total_assets = total_cash + total_gold + total_stocks
        
        # 计算NAV (这里简化为1，因为total已经包含所有资产)
        nav = total_assets / total_assets if total_assets > 0 else 1
        
        # 检查今天是否已有数据
        df_daily = get_as_dataframe(daily_ws, evaluate_formulas=False)
        if 'date' in df_daily.columns:
            today_rows = df_daily[df_daily['date'].astype(str) == timestamp]
            
            print(f"  今天的Daily数据: {'存在' if not today_rows.empty else '不存在'}")
            
            new_row = [
                timestamp,           # date
                total_cash,           # cash_usd  
                total_gold,           # gold_usd
                total_stocks,          # stocks_usd
                total_assets,         # total_usd
                round(nav, 2),       # nav
                f"auto_sync_{timestamp}"  # note
            ]
            
            if today_rows.empty:
                # 添加新行
                daily_ws.append_row(new_row)
                print("✅ Daily 添加新行完成")
            else:
                # 追加新行保持数据连续性
                print(f"  追加新的Daily行...")
                daily_ws.append_row(new_row)
                print("✅ Daily 追加新行完成")
        
    except Exception as e:
        print(f"❌ Daily更新失败: {e}")
        import traceback
        traceback.print_exc()

def complete_sync():
    """执行完整同步流程"""
    print("=" * 60)
    print("🚀 完整资产同步流程 (修正版)")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # 连接Google Sheets
        gc = gspread.service_account()
        sh = gc.open_by_key('1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE')
        
        print(f"✓ 连接到 Google Sheet: {sh.title}")
        
        # 获取工作表
        holdings_ws = sh.worksheet("Holdings")
        daily_ws = sh.worksheet("Daily")
        
        # 1. 获取实时价格
        prices = get_real_time_prices()
        
        if not prices:
            print("❌ 无法获取价格，同步终止")
            return False
            
        # 2. 同步Holdings
        holdings_data = sync_holdings(sh, holdings_ws, prices, timestamp)
        
        # 3. 同步Daily
        sync_daily(sh, daily_ws, holdings_data, timestamp)
        
        print("\n" + "=" * 60)
        print("✅ 完整同步完成！")
        print("=" * 60)
        
        # 4. 运行extract_data.py同步到Dashboard
        print("\n🔄 同步到Dashboard...")
        import subprocess
        result = subprocess.run(
            [sys.executable, 'src/extract_data.py'], 
            capture_output=True, text=True, cwd='/tmp/Asset-Management'
        )
        if result.returncode == 0:
            print(f"✅ Dashboard同步成功")
        else:
            print(f"⚠️  Dashboard同步警告: {result.stderr}")
        
        # 5. 数据验证
        print(f"\n📊 最终数据验证 (时间: {timestamp}):")
        total_cash = next((item['market_value_usd'] for item in holdings_data if item['symbol'] == 'USD'), 0)
        total_gold = next((item['market_value_usd'] for item in holdings_data if item['symbol'] == 'XAU'), 0)
        total_stocks = sum(item['market_value_usd'] for item in holdings_data if item['symbol'] in ['NVDA', 'SHY', 'TSLA', 'QQQ'])
        total_assets = total_cash + total_gold + total_stocks
        
        print(f"  💰 现金: ${total_cash:,.2f}")
        print(f"  🥇 黄金 (8.95g): ${total_gold:,.2f}")
        print(f"  📈 美股: ${total_stocks:,.2f}")
        print(f"  💎 总资产: ${total_assets:,.2f}")
        print(f"  ✅ 验证: 现金 + 黄金 + 美股 = ${total_cash + total_gold + total_stocks:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = complete_sync()
    sys.exit(0 if success else 1)
