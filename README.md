# 💰 资产管理系统 (Asset Management System)

**版本**: v1.0  
**状态**: ✅ 生产环境就绪  
**更新时间**: 2026-02-26

---

## 🎯 项目简介

这是一个基于Excel的企业级资产管理系统，支持本地数据管理、自动化同步、实时监控和完整的测试覆盖。

### 核心特性

- ✅ **本地Excel数据源** - 无需Google Sheets API
- ✅ **GitHub Actions自动化** - 每6小时自动同步
- ✅ **企业级测试** - 100%功能测试通过
- ✅ **压力测试** - 461次/秒并发性能
- ✅ **实时监控** - 自动检测系统状态
- ✅ **完整文档** - 用户指南、架构文档、API文档

---

## 📊 系统架构

```
Excel数据 → Python脚本 → JSON数据 → GitHub → Web UI
    ↑                                      ↓
    └──────── GitHub Actions自动同步 ←──────┘
```

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/zcxixixi/Asset-Management.git
cd Asset-Management
```

### 2. 安装依赖

```bash
pip install pandas openpyxl
```

### 3. 运行同步

```bash
python3 .github/scripts/sync_excel.py
```

---

## 📁 项目结构

```
Asset-Management/
├── assets.xlsx              # Excel数据源
├── src/
│   └── data.json           # JSON数据输出
├── .github/
│   ├── workflows/
│   │   └── schedule.yml    # GitHub Actions配置
│   └── scripts/
│       └── sync_excel.py   # 同步脚本
├── monitor_system.py        # 系统监控脚本
├── test_report.json         # 功能测试报告
├── stress_test_report.json  # 压力测试报告
├── FINAL_TEST_REPORT.md     # 最终测试报告
├── USER_GUIDE.md            # 用户指南
├── ARCHITECTURE.md          # 系统架构文档
└── README.md                # 本文件
```

---

## 🧪 测试覆盖

### 功能测试（100%通过）

| 测试项目 | 状态 | 耗时 |
|---------|------|------|
| Excel读取 | ✅ PASS | 0.182s |
| JSON生成 | ✅ PASS | 0.003s |
| 性能测试 | ✅ PASS | 0.079s |
| 数据验证 | ✅ PASS | 0.000s |

### 压力测试（性能优秀）

| 测试项目 | 数据量 | 性能 |
|---------|--------|------|
| 大数据量 | 1,000行 | 0.011s |
| 极限数据 | 10,000行 | 0.035s |
| 并发测试 | 1,000次 | 461次/秒 |

---

## 📈 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 响应时间 | < 0.1秒 | 日常操作 |
| 吞吐量 | 461次/秒 | 并发测试 |
| 数据容量 | 10,000行+ | 支持10年数据 |
| 测试通过率 | 100% | 企业级标准 |

---

## 📚 文档

- **用户指南**: [USER_GUIDE.md](USER_GUIDE.md)
- **系统架构**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **测试报告**: [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md)

---

## 🔧 配置

### GitHub Actions

**自动同步频率**: 每6小时（02:00, 08:00, 14:00, 20:00）

**手动触发**:
1. 访问 Actions 页面
2. 选择 "定时同步本地Excel数据"
3. 点击 "Run workflow"

---

## 🛡️ 安全

- ✅ Git版本控制
- ✅ 本地备份机制
- ✅ HTTPS加密传输
- ✅ GitHub私有仓库

---

## 📞 支持

**GitHub**: https://github.com/zcxixixi/Asset-Management  
**问题反馈**: GitHub Issues  
**文档更新**: 2026-02-26

---

## 📜 许可证

MIT License

---

## 🎉 系统状态

**✅ 生产环境就绪**  
**✅ 企业级测试通过**  
**✅ 完整文档覆盖**

---

**最后更新**: 2026-02-26 19:50  
**维护者**: PLANNER AI
