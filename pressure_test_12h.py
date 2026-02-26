#!/usr/bin/env python3
"""
12小时压力检测系统
持续验证数据稳定性：价格、资产、展示
"""
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import os

class PressureTest12H:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=12)
        self.check_count = 0
        self.errors = []
        self.fixes = []
        
    def check_excel_data(self):
        """检查Excel数据完整性"""
        try:
            df = pd.read_excel("assets.xlsx", sheet_name="Daily")
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            # 检查数据完整性
            checks = {
                "rows": len(df),
                "null_dates": df['date'].isna().sum(),
                "null_values": df[['cash_usd', 'gold_usd', 'stocks_usd', 'total_usd']].isna().sum().sum()
            }
            
            # 检查资产一致性
            latest = df.iloc[-1]
            calculated = latest['cash_usd'] + latest['gold_usd'] + latest['stocks_usd']
            diff = abs(calculated - latest['total_usd'])
            
            checks["asset_consistency"] = diff < 0.01
            checks["calculated_total"] = float(calculated)
            checks["recorded_total"] = float(latest['total_usd'])
            checks["difference"] = float(diff)
            
            return checks
        except Exception as e:
            return {"error": str(e)}
    
    def check_json_data(self):
        """检查JSON数据一致性"""
        try:
            with open("src/data.json", "r") as f:
                data = json.load(f)
            
            checks = {
                "has_summary": "summary" in data,
                "has_total": "total_usd" in data.get("summary", {}),
                "timestamp": data.get("last_updated"),
            }
            
            if "summary" in data:
                summary = data["summary"]
                checks["total_value"] = summary.get("total_usd")
            
            return checks
        except Exception as e:
            return {"error": str(e)}
    
    def check_consistency(self):
        """检查Excel和JSON一致性"""
        try:
            df = pd.read_excel("assets.xlsx", sheet_name="Daily")
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            latest_excel = df.iloc[-1]['total_usd']
            
            with open("src/data.json", "r") as f:
                data = json.load(f)
            
            latest_json = data["summary"]["total_usd"]
            
            diff = abs(float(latest_excel) - float(latest_json))
            
            return {
                "excel_total": float(latest_excel),
                "json_total": float(latest_json),
                "difference": float(diff),
                "consistent": diff < 0.01
            }
        except Exception as e:
            return {"error": str(e)}
    
    def fix_data(self):
        """自动修复数据不一致"""
        try:
            # 重新生成JSON
            df = pd.read_excel("assets.xlsx", sheet_name="Daily")
            df['date'] = pd.to_datetime(df['date']).astype(str)
            
            data = {
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "summary": {
                    "total_usd": float(df.iloc[-1]['total_usd']),
                    "cash_usd": float(df.iloc[-1]['cash_usd']),
                    "gold_usd": float(df.iloc[-1]['gold_usd']),
                    "stocks_usd": float(df.iloc[-1]['stocks_usd']),
                    "date": df.iloc[-1]['date']
                }
            }
            
            with open("src/data.json", "w") as f:
                json.dump(data, f, indent=2)
            
            return {"status": "fixed", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        except Exception as e:
            return {"error": str(e)}
    
    def run_check_cycle(self):
        """运行一次完整检查周期"""
        self.check_count += 1
        
        report = {
            "check_number": self.check_count,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "elapsed_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "remaining_hours": (self.end_time - datetime.now()).total_seconds() / 3600,
            "checks": {}
        }
        
        # 1. 检查Excel数据
        report["checks"]["excel"] = self.check_excel_data()
        
        # 2. 检查JSON数据
        report["checks"]["json"] = self.check_json_data()
        
        # 3. 检查一致性
        report["checks"]["consistency"] = self.check_consistency()
        
        # 4. 检查是否有错误
        has_error = any(
            "error" in check or (isinstance(check, dict) and not check.get("consistent", True))
            for check in report["checks"].values()
        )
        
        if has_error:
            report["fix"] = self.fix_data()
            self.fixes.append(report)
        
        return report
    
    def save_report(self, report):
        """保存报告"""
        filename = f"pressure_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)
        return filename

if __name__ == "__main__":
    test = PressureTest12H()
    
    print("=" * 60)
    print("🚀 12小时压力检测开始")
    print(f"开始时间: {test.start_time}")
    print(f"结束时间: {test.end_time}")
    print("=" * 60)
    print()
    
    # 运行单次检查
    report = test.run_check_cycle()
    
    print(f"检查 #{report['check_number']}")
    print(f"时间: {report['timestamp']}")
    print(f"已运行: {report['elapsed_hours']:.2f}小时")
    print(f"剩余: {report['remaining_hours']:.2f}小时")
    print()
    
    print("Excel检查:")
    for key, value in report["checks"]["excel"].items():
        print(f"  {key}: {value}")
    
    print()
    print("JSON检查:")
    for key, value in report["checks"]["json"].items():
        print(f"  {key}: {value}")
    
    print()
    print("一致性检查:")
    for key, value in report["checks"]["consistency"].items():
        print(f"  {key}: {value}")
    
    if "fix" in report:
        print()
        print("🔧 数据已修复:")
        print(f"  {report['fix']}")
    
    print()
    filename = test.save_report(report)
    print(f"✅ 报告已保存: {filename}")
    print("=" * 60)

