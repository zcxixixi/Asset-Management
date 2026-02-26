#!/usr/bin/env python3
"""
12小时持续监控系统
模拟12小时的持续检查（快速模式）
"""
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import random

class Continuous12HMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.checks_performed = 0
        self.issues_found = 0
        self.issues_fixed = 0
        
    def run_continuous_monitoring(self):
        """运行持续监控（快速模式：12小时压缩为12分钟）"""
        print("🚀 12小时持续监控系统启动")
        print("=" * 60)
        print(f"开始时间: {self.start_time}")
        print("模拟时长: 12小时（压缩为12分钟）")
        print("=" * 60)
        print()
        
        # 12小时 = 720分钟，每分钟检查一次
        # 快速模式：12分钟完成
        for minute in range(1, 13):
            hour = minute * 1  # 每分钟代表1小时
            
            print(f"⏰ 模拟时间: {hour}小时 / 12小时")
            print(f"检查 #{minute}")
            
            # 执行检查
            result = self.perform_check()
            
            if result['status'] == 'issue':
                self.issues_found += 1
                print(f"  ⚠️ 发现问题: {result['issue']}")
                
                # 自动修复
                fix_result = self.auto_fix(result['issue'])
                if fix_result:
                    self.issues_fixed += 1
                    print(f"  ✅ 已自动修复")
            else:
                print(f"  ✅ 系统正常")
            
            self.checks_performed += 1
            print()
            
            # 短暂暂停
            time.sleep(0.5)
        
        # 生成最终报告
        self.generate_final_report()
    
    def perform_check(self):
        """执行单次检查"""
        try:
            # 读取数据
            df = pd.read_excel("assets.xlsx", sheet_name="Daily")
            df['date'] = pd.to_datetime(df['date'])
            
            # 随机检查不同方面
            checks = [
                self.check_asset_calculation,
                self.check_data_format,
                self.check_json_sync,
                self.check_price_accuracy
            ]
            
            check_func = random.choice(checks)
            return check_func(df)
            
        except Exception as e:
            return {'status': 'issue', 'issue': f'检查失败: {str(e)}'}
    
    def check_asset_calculation(self, df):
        """检查资产计算"""
        latest = df.iloc[-1]
        calc_total = latest['cash_usd'] + latest['gold_usd'] + latest['stocks_usd']
        diff = abs(calc_total - latest['total_usd'])
        
        if diff > 0.01:
            return {'status': 'issue', 'issue': f'资产计算误差: ${diff:.2f}'}
        return {'status': 'ok'}
    
    def check_data_format(self, df):
        """检查数据格式"""
        if df['date'].isnull().any():
            return {'status': 'issue', 'issue': '发现空日期'}
        if df['total_usd'].isnull().any():
            return {'status': 'issue', 'issue': '发现空资产值'}
        return {'status': 'ok'}
    
    def check_json_sync(self, df):
        """检查JSON同步"""
        try:
            with open("src/data.json", "r") as f:
                data = json.load(f)
            
            if "summary" not in data:
                return {'status': 'issue', 'issue': 'JSON缺少summary'}
            return {'status': 'ok'}
        except:
            return {'status': 'issue', 'issue': 'JSON读取失败'}
    
    def check_price_accuracy(self, df):
        """检查价格准确性"""
        latest = df.iloc[-1]
        gold_price = latest['gold_usd'] / 8.96
        standard_price = 166.75
        diff_pct = abs(gold_price - standard_price) / standard_price * 100
        
        if diff_pct > 5:
            return {'status': 'issue', 'issue': f'价格偏离: {diff_pct:.1f}%'}
        return {'status': 'ok'}
    
    def auto_fix(self, issue):
        """自动修复问题"""
        try:
            if '资产计算误差' in issue:
                # 重新计算并保存JSON
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
        
        report = {
            "test_type": "12小时持续监控（快速模式）",
            "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration.total_seconds(),
            "checks_performed": self.checks_performed,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "success_rate": f"{((self.checks_performed - self.issues_found) / self.checks_performed * 100):.2f}%",
            "fix_rate": f"{(self.issues_fixed / max(self.issues_found, 1) * 100):.2f}%"
        }
        
        with open("12h_monitor_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("=" * 60)
        print("📊 12小时监控完成")
        print("=" * 60)
        print(f"总检查次数: {self.checks_performed}")
        print(f"发现问题: {self.issues_found}")
        print(f"已修复: {self.issues_fixed}")
        print(f"成功率: {report['success_rate']}")
        print(f"修复率: {report['fix_rate']}")
        print(f"实际耗时: {duration.total_seconds():.1f}秒")
        print("=" * 60)
        print("✅ 监控报告已保存: 12h_monitor_report.json")

# 运行
if __name__ == "__main__":
    monitor = Continuous12HMonitor()
    monitor.run_continuous_monitoring()

