#!/usr/bin/env python3
"""
Google Sheets API 权限检查脚本
测试服务账号是否有完整的读写权限
"""
import gspread
from gspread.exceptions import APIError

def check_permissions():
    """检查Google Sheets API权限"""
    print("=" * 60)
    print("🔍 Google Sheets API 权限检查")
    print("=" * 60)
    print()
    
    try:
        # 1. 认证
        gc = gspread.service_account()
        print("✓ 1/4 Service account认证成功")
        
        # 2. 打开Sheet
        sh = gc.open_by_key('1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE')
        print(f"✓ 2/4 成功打开Sheet: {sh.title}")
        
        # 3. 读取测试
        daily_ws = sh.worksheet("Daily")
        cell_value = daily_ws.acell('A1').value
        print(f"✓ 3/4 可以读取单元格 A1: {cell_value[:30]}")
        
        # 4. 更新测试
        print()
        print("正在测试更新权限...")
        try:
            # 使用最后一行的备注列进行测试
            test_note = f"权限测试_{__import__('time').strftime('%Y%m%d_%H%M%S')}"
            daily_ws.update_acell('G2', test_note)
            print("✓ 4/4 可以更新单元格 G2")
            print()
            print("=" * 60)
            print("✅ 权限检查通过 - 所有操作正常")
            print("=" * 60)
            print()
            print("🚀 可以正常运行同步脚本:")
            print("   python3 /tmp/Asset-Management/sync_daily.py")
            
            # 恢复原值
            daily_ws.update_acell('G2', 'fixed_qty+sge:2026-02-13')
            
            return True
            
        except APIError as e:
            if "403" in str(e):
                print("✗ 4/4 无法更新单元格 (返回[403])")
                print()
                print("=" * 60)
                print("❌ 权限不足 - 只有读取权限")
                print("=" * 60)
                print()
                print("📋 需要执行以下步骤:")
                print("   1. 打开Google Sheet")
                print("   2. 点击Share")
                print("   3. 添加: asset-sync@assettracker-487204.iam.gserviceaccount.com")
                print("   4. 设置为 Editor (编辑者)")
                print("   5. 点击 Send")
                print()
                print("✅ 完成后重新运行此脚本验证")
                return False
            else:
                raise
                
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = check_permissions()
    sys.exit(0 if success else 1)
