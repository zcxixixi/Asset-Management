# 🚀 快速部署指南

**立即开始使用**

## 步骤1：确保数据存在

```bash
# 检查assets.xlsx
ls -lh assets.xlsx

# 如果不存在，从桌面复制
cp ~/Desktop/dashboard-demo/public/assets.xlsx .
```

## 步骤2：手动同步（最可靠）

```bash
# 进入项目目录
cd /tmp/Asset-Management

# 同步数据
python3 assets_check.py

# 提交
git add src/data.json
git commit -m "data"
git push
```

## 步骤3：验证

```bash
# 访问GitHub
open https://github.com/zcxixixi/Asset-Management

# 查看src/data.json是否更新
```

---

## ✅ 完成

**总资产**: $5,202.84  
**最新日期**: 2026-02-23

---
