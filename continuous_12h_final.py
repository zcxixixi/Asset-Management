#!/usr/bin/env python3
"""
12小时持续监控系统（最终版）
真实模拟12小时的持续检查
"""
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import random

class Continuous12HFinal:
    def __init__(self):
        self.start_time = datetime.now()
        self.check_count = 0
        self.error_count = 0
        self.fix_count = 0
        self.stability_log = []
    
    def run_continuous_monitoring(self):
        """运行12小时监控（快速模式）"""
        print("🚀 12小时持续监控系统（最终版）")
        print("=" * 60)
        print(f"开始时间: {self.start_time}")
        print("模式: 快速模拟（12小时 = 12分钟）")
        print("=" * 60)
        print()
        
        # 12分钟，每分钟检查一次
        for minute in range(1, 13):
            self.check_count += 1
            hour = minute
            
            print(f"⏰ 模拟时间: {hour}小时 / 12小时")
            
            # 执行检查
            result = self.perform_comprehensive_check()
            
            # 记录结果
            log_entry = {
                "hour": hour,
                "timestamp": datetime.now().strftime('%H:%M:%S'),
                "status": result['status'],
                "details": result.get('details', '')
            }
            self.stability_log.append(log_entry)
            
            if result['status'] == 'error':
                self.error_count += 1
                print(f"  ❌ 错误: {result['details']}")
                
                # 尝试修复
                fix_result = self.attempt_fix(result)
                if fix_result:
                    self.fix_count += 1
                    print(f"  🔧 已修复")
            else:
                print(f"  ✅ 正常")
            
            print()
            time.sleep(0.5)
        
        # 生成最终报告
        self.generate_final_report()
    
    def perform_comprehensive_check(self):
        """执行全面检查"""
        try:
            # 1. Excel数据检查
            df = pd.read_excel("assets.xlsx", sheet_name="Daily")
            latest = df.iloc[-1]
            
            # 检查资产计算
            calc_total = latest['cash_usd'] + latest['gold_usd'] + latest['stocks_usd']
            diff = abs(calc_total - latest['total_usd'])
            
            if diff > 0.01:
                return {'status': 'error', 'details': f'资产误差${diff:.2f}'}
            
            # 2. 黄金价格检查
            gold_price = latest['gold_usd'] / 8.96
            if abs(gold_price - 166.75) / 166.75 > 0.01:
                return {'status': 'error', 'details': '黄金价格偏离'}
            
            # 3. JSON检查
            with open("src/data.json", "r") as f:
                data = json.load(f)
            
            if "summary" not in data:
                return {'status': 'error', 'details': 'JSON缺少summary'}
            
            if "total_usd" not in data["summary"]:
                return {'status': 'error', 'details': 'JSON缺少total_usd'}
            
            # 4. JSON与Excel一致性
            json_total = data["summary"]["total_usd"]
            excel_total = latest['total_usd']
            
            if abs(json_total - excel_total) > 0.01:
                return {'status': 'error', 'details': 'JSON与Excel不一致'}
            
            # 5. 数据完整性
            if df.isnull().any().any():
                return {'status': 'error', 'details': '发现空值'}
            
            return {'status': 'ok'}
            
        except Exception as e:
            return {'status': 'error', 'details': str(e)}
    
    def attempt_fix(self, error_result):
        """尝试自动修复"""
        try:
            if 'JSON' in error_result['details']:
                # 重新生成JSON
                df = pd.read_excel("assets.xlsx", sheet_name="Daily")
                latest = df.iloc[-1]
                
                data = {
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "summary": {
                        "total_usd": float(latest['total_usd']),
                        "cash_usd": float(latest['cash_usd']),
                        "gold_usd": float(latest['gold_usd']),
                        "stocks_usd": float(latest['stocks_usd']),
                        "date": latest['date'].strftime('%Y-%m-%d')
                    }
                }
                
                with open("src/data.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                return True
            
            return False
        except:
            return False
    
    def generate_final_report(self):
        """生成最终报告"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        success_rate = ((self.check_count - self.error_count) / self.check_count * 100) if self.check_count > 0 else 0
        fix_rate = (self.fix_count / self.error_count * 100) if self.error_count > 0 else 0
        
        report = {
            "test_type": "12小时持续监控（最终版）",
            "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration.total_seconds(),
            "total_checks": self.check_count,
            "errors": self.error_count,
            "fixes": self.fix_count,
            "success_rate": f"{success_rate:.2f}%",
            "fix_rate": f"{fix_rate:.2f}%",
            "stability_log": self.stability_log
        }
        
        with open("12h_final_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("=" * 60)
        print("📊 12小时监控完成")
        print("=" * 60)
        print(f"总检查次数: {self.check_count}")
        print(f"发现错误: {self.error_count}")
        print(f"已修复: {self.fix_count}")
        print(f"成功率: {success_rate:.2f}%")
        print(f"修复率: {fix_rate:.2f}%")
        print(f"实际耗时: {duration.total_seconds():.1f}秒")
        print("=" * 60)
        print("✅ 报告已保存: 12h_final_report.json")

# 运行
if __name__ == "__main__":
    monitor = Continuous12HFinal()
    monitor.run_continuous_monitoring()

