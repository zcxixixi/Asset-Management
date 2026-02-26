# 🔧 故障排除指南

**版本**: v1.0  
**更新时间**: 2026-02-26

---

## 🚨 常见问题

### 1. GitHub Actions失败

**症状**: 工作流执行失败

**原因**:
- Excel文件不存在
- Python依赖安装失败
- 脚本执行错误

**解决方案**:
```bash
# 1. 检查文件是否存在
ls -lh assets.xlsx

# 2. 本地测试脚本
python3 .github/scripts/sync_excel.py

# 3. 检查GitHub Actions日志
# 访问: https://github.com/zcxixixi/Asset-Management/actions
```

---

### 2. Excel文件无法读取

**症状**: 脚本报错"Excel文件不存在"

**原因**:
- 文件路径错误
- 文件未提交到Git
- 文件损坏

**解决方案**:
```bash
# 1. 检查文件路径
ls -la assets.xlsx

# 2. 重新添加文件
git add assets.xlsx
git commit -m "fix: 添加Excel文件"
git push

# 3. 验证文件完整性
python3 -c "import pandas as pd; df = pd.read_excel('assets.xlsx'); print(df.head())"
```

---

### 3. JSON生成失败

**症状**: data.json未生成或数据错误

**原因**:
- 数据类型问题（Timestamp）
- 权限问题
- 磁盘空间不足

**解决方案**:
```bash
# 1. 检查磁盘空间
df -h

# 2. 检查权限
chmod 644 src/data.json

# 3. 重新生成
python3 .github/scripts/sync_excel.py
```

---

### 4. Git推送失败

**症状**: git push失败

**原因**:
- 网络问题
- 权限问题
- 冲突问题

**解决方案**:
```bash
# 1. 检查网络
ping github.com

# 2. 检查Git状态
git status

# 3. 解决冲突
git pull --rebase
git push
```

---

## 🛠️ 调试工具

### 1. 系统状态检查

```bash
cd /tmp/Asset-Management
python3 monitor_system.py
```

### 2. 本地测试

```bash
cd /tmp/Asset-Management
python3 .github/scripts/sync_excel.py
```

### 3. Git检查

```bash
cd /tmp/Asset-Management
git status
git log --oneline -5
```

---

## 📞 获取帮助

1. **检查文档**: README.md, USER_GUIDE.md
2. **查看日志**: GitHub Actions日志
3. **提交Issue**: GitHub Issues
4. **本地测试**: 运行monitor_system.py

---

## 🎯 预防措施

1. **定期备份**: 备份assets.xlsx
2. **监控日志**: 定期检查GitHub Actions
3. **本地测试**: 修改后先本地测试
4. **版本控制**: 每次修改后及时commit

---

**更新时间**: 2026-02-26  
**维护者**: PLANNER AI
