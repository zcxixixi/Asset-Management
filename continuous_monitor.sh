#!/bin/bash
# 持续监控脚本

echo "🔍 开始持续监控..."
echo "按Ctrl+C停止"

while true; do
    clear
    echo "📊 系统监控 - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================================="
    echo ""
    
    # 检查Git状态
    echo "✅ Git状态:"
    git status --short
    echo ""
    
    # 检查文件
    echo "✅ 文件检查:"
    ls -lh assets.xlsx src/data.json 2>/dev/null || echo "❌ 文件缺失"
    echo ""
    
    # 检查最新提交
    echo "✅ 最新提交:"
    git log -1 --oneline
    echo ""
    
    echo "=================================================="
    echo "下次检查: 60秒后 | Ctrl+C停止"
    
    sleep 60
done
