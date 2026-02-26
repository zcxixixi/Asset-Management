#!/usr/bin/env python3
"""
简化同步测试 - 测试基本功能
"""
import gspread
from datetime import datetime

def test_basic_sync():
    """测试基本同步功能"""
    print("=" * 50)
    print("🔧 基本同步功能测试")
    print("=" * 50)
    
    try:
        # 连接
        gc = gspread.service_account()
        sh = gc.open_by_key('1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE')
        print("✓ 连接成功")
        
        # 获取工作表
        holdings_ws = sh.worksheet("Holdings")
        daily_ws = sh.worksheet("Daily")
        print("✓ 获取工作表成功")
        
        # 准备测试数据
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        # Holdings 测试数据
        holdings_data = [
            ['name', 'quantity', 'symbol', 'market_value_usd'],
            ['NVIDIA Corp', '0.73', 'NVDA', '85500.00'],  # 假设价格$117123
            ['iShares 0-3 Month Treasury Bond ETF', '15.14', 'SHY', '15140.00'],
            ['Tesla, Inc.', '1.23', 'TSLA', '24600.00'],  # 假设价格$20000
            ['NASDAQ 100 ETF', '1.73', 'QQQ', '17300.00'],
            ['Cash', '571.73', 'USD', '571.73'],
            ['Gold (ETF-linked)', '8.95', 'XAU', '1498.00']  # 根据之前计算
        ]
        
        # Daily 测试数据
        daily_data = [
            ['date', 'cash_usd', 'gold_usd', 'stocks_usd', 'total_usd', 'nav', 'note'],
            [timestamp, 571.73, 1498.00, 127440.00, 129509.73, 1.11, f'test_sync_{timestamp}']
        ]
        
        # 更新 Holdings
        print("📊 更新 Holdings...")
        holdings_ws.clear()
        for row in holdings_data:
            holdings_ws.append_row(row)
        print("✅ Holdings 更新完成")
        
        # 更新 Daily
        print("📅 更新 Daily...")
        daily_ws.clear()
        for row in daily_data:
            daily_ws.append_row(row)
        print("✅ Daily 更新完成")
        
        # 运行 extract_data
        print("🔄 运行 extract_data.py...")
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, 'src/extract_data.py'],
            capture_output=True, text=True,
            cwd='/tmp/Asset-Management'
        )
        print(f"结果: {result.stdout.strip()}")
        if result.stderr:
            print(f"错误: {result.stderr}")
        
        print("\n" + "=" * 50)
        print("✅ 测试同步完成！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_basic_sync()
    sys.exit(0 if success else 1)
