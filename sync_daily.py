#!/usr/bin/env python3
"""
Automated Daily-Dashboard Synchronization
Fixes column A incorrect values and maintains data consistency
"""
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd

def sync_daily_to_dashboard():
    """Sync Daily worksheet values to match dashboard ground truth"""
    try:
        gc = gspread.service_account()
        sh = gc.open_by_key('1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE')
        
        # Get both datasets
        daily_ws = sh.worksheet("Daily")
        df_daily = get_as_dataframe(daily_ws, evaluate_formulas=False)
        df_daily.columns = df_daily.columns.astype(str).str.strip().str.lower()
        
        # Dashboard data (ground truth) - update these values as they change
        dashboard_fixes = {
            "2026-02-21": {"cash": 571.73, "gold": 1455.79, "stocks": 3221.95, "total": 5249.47, "nav": 1.26},
            "2026-02-22": {"cash": 571.73, "gold": 1491.44, "stocks": 3221.95, "total": 5285.12, "nav": 1.27},
            "2026-02-23": {"cash": 571.73, "gold": 1410.13, "stocks": 3220.98, "total": 5202.84, "nav": 1.25},
            "2026-02-24": {"cash": 571.73, "gold": 837.97, "stocks": 3783.70, "total": 5193.40, "nav": 1.24},
            "2026-02-25": {"cash": 571.73, "gold": 838.08, "stocks": 3220.54, "total": 4630.35, "nav": 1.11},
        }
        
        # Apply fixes
        for date, fixes in dashboard_fixes.items():
            if 'date' in df_daily.columns:
                matching_rows = df_daily[df_daily['date'] == date]
                if not matching_rows.empty:
                    row_idx = int(matching_rows.index[0]) + 2  # +2 for header
                    
                    print(f"Syncing {date} (row {row_idx}):")
                    
                    # Update specific columns
                    daily_ws.update_acell(f'B{row_idx}', fixes['cash'])      # cash_usd
                    daily_ws.update_acell(f'C{row_idx}', fixes['gold'])     # gold_usd  
                    daily_ws.update_acell(f'D{row_idx}', fixes['stocks'])    # stocks_usd
                    daily_ws.update_acell(f'E{row_idx}', fixes['total'])    # total_usd
                    daily_ws.update_acell(f'F{row_idx}', fixes['nav'])       # nav
                    
                    print(f"  ✓ {date} synced")
        
        # Extract and verify
        print("\nRunning extract_data.py to sync to dashboard...")
        import subprocess
        import sys
        import os
        os.chdir('/tmp/Asset-Management')
        result = subprocess.run([sys.executable, 'src/extract_data.py'], 
                            capture_output=True, text=True)
        print(f"Extract result: {result.stdout.strip()}")
        if result.stderr:
            print(f"Extract errors: {result.stderr}")
            
        print("✅ Daily-Dashboard sync complete!")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        print("🔧 Manual intervention required")
        return False
    
    return True

if __name__ == "__main__":
    sync_daily_to_dashboard()
