#!/usr/bin/env python3
"""
系统监控脚本
每5分钟检查一次系统状态
"""
import os
import json
import time
from datetime import datetime

def check_system():
    """检查系统状态"""
    status = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "checks": []
    }
    
    # 检查1: Excel文件存在
    excel_exists = os.path.exists("assets.xlsx")
    status["checks"].append({
        "name": "Excel文件",
        "status": "OK" if excel_exists else "ERROR",
        "details": "存在" if excel_exists else "不存在"
    })
    
    # 检查2: JSON文件存在
    json_exists = os.path.exists("src/data.json")
    status["checks"].append({
        "name": "JSON文件",
        "status": "OK" if json_exists else "ERROR",
        "details": "存在" if json_exists else "不存在"
    })
    
    # 检查3: Git仓库状态
    git_clean = os.system("git diff --quiet") == 0
    status["checks"].append({
        "name": "Git仓库",
        "status": "OK" if git_clean else "WARNING",
        "details": "干净" if git_clean else "有未提交更改"
    })
    
    # 保存状态
    with open("system_status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    return status

if __name__ == "__main__":
    print("🔍 系统监控启动")
    print("=" * 50)
    
    status = check_system()
    
    print(f"⏰ 时间: {status['timestamp']}")
    print()
    
    for check in status["checks"]:
        emoji = "✅" if check["status"] == "OK" else "⚠️" if check["status"] == "WARNING" else "❌"
        print(f"{emoji} {check['name']}: {check['details']}")
    
    print()
    print("=" * 50)
    print("✅ 监控完成")

