# 📚 资产管理系统 - 用户指南

**版本**: v1.0  
**更新时间**: 2026-02-26

---

## 🎯 系统概述

这是一个基于Excel的企业级资产管理系统，支持：
- ✅ 本地Excel数据源
- ✅ GitHub Actions自动化同步（每6小时）
- ✅ 实时监控和报警
- ✅ 企业级测试和压力测试
- ✅ Git版本控制

---

## 🚀 快速开始

### 1. 数据更新

**手动更新Excel**：
```bash
# 1. 修改本地Excel文件
open ~/Desktop/dashboard-demo/public/assets.xlsx

# 2. 同步到Git仓库
cd /tmp/Asset-Management
cp ~/Desktop/dashboard-demo/public/assets.xlsx .
python3 .github/scripts/sync_excel.py
git add assets.xlsx src/data.json
git commit -m "📊 更新资产数据"
git push
```

### 2. 查看数据

**访问JSON数据**：
- GitHub: https://github.com/zcxixixi/Asset-Management/blob/main/src/data.json
- 本地: `/tmp/Asset-Management/src/data.json`

---

## 📊 数据结构

### Excel文件（assets.xlsx）

**Daily工作表**：
- date: 日期（YYYY-MM-DD）
- cash_usd: 现金（USD）
- gold_usd: 黄金（USD）
- stocks_usd: 美股（USD）
- total_usd: 总资产（USD）
- nav: 净值
- note: 备注

**Holdings工作表**：
- timestamp: 时间戳
- account: 账户
- symbol: 代码
- name: 名称
- quantity: 数量
- price_usd: 价格（USD）
- market_value_usd: 市值（USD）

---

## ⚙️ 自动化配置

### GitHub Actions

**工作流文件**: `.github/workflows/schedule.yml`

**执行频率**: 每6小时（北京时间 02:00, 08:00, 14:00, 20:00）

**手动触发**:
1. 访问 https://github.com/zcxixixi/Asset-Management/actions
2. 选择 "定时同步本地Excel数据"
3. 点击 "Run workflow"

---

## 🔍 系统监控

### 运行监控脚本

```bash
cd /tmp/Asset-Management
python3 monitor_system.py
```

**监控项目**：
- ✅ Excel文件存在
- ✅ JSON文件存在
- ✅ Git仓库状态

---

## 🧪 测试报告

### 查看测试结果

**功能测试**: `test_report.json`  
**压力测试**: `stress_test_report.json`  
**最终报告**: `FINAL_TEST_REPORT.md`

### 运行测试

```bash
cd /tmp/Asset-Management
python3 test_enterprise.py
```

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 响应时间 | < 0.1秒 |
| 并发性能 | 461次/秒 |
| 数据容量 | 10,000行+ |
| 通过率 | 100% |

---

## 🛠️ 故障排除

### 问题1: Excel文件无法读取

**解决方案**:
```bash
# 检查文件是否存在
ls -lh assets.xlsx

# 检查文件权限
chmod 644 assets.xlsx
```

### 问题2: JSON生成失败

**解决方案**:
```bash
# 检查Python依赖
pip install pandas openpyxl

# 重新生成JSON
python3 .github/scripts/sync_excel.py
```

### 问题3: Git推送失败

**解决方案**:
```bash
# 检查Git状态
git status

# 重新提交
git add -A
git commit -m "fix: 修复问题"
git push
```

---

## 📞 支持

**GitHub仓库**: https://github.com/zcxixixi/Asset-Management  
**问题反馈**: GitHub Issues  
**文档更新**: 2026-02-26

---

**系统状态**: ✅ 生产环境就绪
