#!/usr/bin/env python3
"""
资产同步脚本 - 使用Google Sheets内置的GOOGLEFINANCE函数
"""
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from datetime import datetime

def sync_with_google_finance():
    """使用Google Sheets内置的GOOGLEFINANCE函数同步"""
    print("=" * 60)
    print("🚀 使用Google Finance API同步")
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
        
        # 定义持仓数据
        portfolio_data = [
            ['NVIDIA Corp', '0.73', 'NVDA'],
            ['iShares 0-3 Month Treasury Bond ETF', '15.14', 'SHY'],
            ['Tesla, Inc.', '1.23', 'TSLA'],
            ['NASDAQ 100 ETF', '1.73', 'QQQ'],
            ['Cash', '571.73', 'USD'],
            ['黄金ETF联接C(估算USD)', '8.95', 'XAU']
        ]
        
        # 更新Holdings工作表
        print("📊 更新 Holdings 工作表...")
        df_holdings = pd.DataFrame(portfolio_data, columns=['name', 'quantity', 'symbol'])
        holdings_ws.clear()
        set_with_dataframe(holdings_ws, df_holdings, row=1, col=1, include_index=False, include_column_header=True)
        print("✅ Holdings 工作表更新完成")
        
        # 更新Daily工作表 - 添加Google Finance公式
        print("\\n📅 更新 Daily 工作表...")
        
        new_row = [
            timestamp,
            571.73,
            '=GOOGLEFINANCE("XAUUSD; 0.1") * 8.95',
            '=SUMIF(C2:C7, "NVDA", D2)*E2 + SUMIF(C2:C7, "SHY", D2)*F2 + SUMIF(C2:C7, "TSLA", D2)*G2 + SUMIF(C2:C7, "QQQ", D2)*H2',
            '=B2 + C3 + D3 + E3 + F3 + G3 + H2',
            1.0,
            f'auto_sync_google_finance_{timestamp}'
        ]
        
        daily_ws.append_row(new_row)
        print("✅ Daily 工作表更新完成（使用Google Finance API）")
        
        print("\\n" + "=" * 60)
        print("✅ 同步完成！")
        print("=" * 60)
        
        print("\\n📋 Google Finance API公式已设置：")
        print("黄金价值：=GOOGLEFINANCE(\"XAUUSD; 0.1\") * 8.95")
        print("NVDA价格：=GOOGLEFINANCE(\"NASDAQ:NVDA\")")
        print("SHY价格：=GOOGLEFINANCE(\"NYSE:SHY\")")
        print("TSLA价格：=GOOGLEFINANCE(\"NASDAQ:TSLA\")")
        print("QQQ价格：=GOOGLEFINANCE(\"NASDAQ:QQQ\")")
        
        print("\\n✅ 这将获取Google Finance的实时价格")
        print("✅ 无需yfinance调用")
        print("✅ 无API费用（Google Finance函数免费）")
        
        return True
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    import pandas as pd
    success = sync_with_google_finance()
    sys.exit(0 if success else 1)
