# 架构

## 定位

Android App 自动化测试平台。核心流程：

```
拉取远程仓库 → 代码静态分析 → 测试生成 → 测试执行 → 报告输出
```

## 分层架构

```
CLI / GUI  →  Pipeline（编排）
                  ↓
    repo / analyzer / generator / runner / reporter
                  ↓
    Storage (SQLite + 截图文件系统)
```

## 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| config | 配置加载 | YAML | Config 对象 |
| repo | 仓库管理 | URL + branch | 本地代码目录 |
| analyzer | 代码分析 | 源码目录 | AST/依赖图/类信息 |
| generator/unit | 单元测试生成 | 分析结果 | JUnit 测试文件 |
| generator/manual | 人工用例生成 | 分析结果 + 模板 | YAML 用例文件 |
| generator/e2e | E2E 脚本生成 | 页面信息 + 流程 | Python 自动化脚本 |
| runner/unit | 单元测试执行 | 测试文件 | 执行结果 |
| runner/ui | UI 自动化执行 | 脚本 + 设备 | 执行结果 + 截图 |
| runner/stability | 稳定性测试 | 配置 + 设备 | 崩溃日志 |
| runner/opencv | UI 对比 | 截图 + 基线 | 差异报告 |
| reporter | 报告生成 | 执行结果 | HTML/JSON 报告 |
| storage | 持久化 | 用例/结果/截图 | SQLite + 文件 |
| utils | 工具 | — | ADB/截图/日志 |

## 测试层级

```
┌─────────────────────────────────────┐
│         稳定性测试 (Monkey)          │  ← 最粗粒度
├─────────────────────────────────────┤
│    UI 自动化 (uiautomator2/Appium)   │
├─────────────────────────────────────┤
│      OpenCV UI 对比 (视觉回归)       │
├─────────────────────────────────────┤
│     人工测试用例 (业务流程验证)       │
├─────────────────────────────────────┤
│   单元测试 (JUnit/Robolectric)       │  ← 最细粒度
└─────────────────────────────────────┘
```

## 关键决策

- D-001 代码分析用 Python AST（Java/Kotlin 用 javalang/tree-sitter）
- D-002 UI 自动化优先 uiautomator2（轻量），复杂场景 fallback Appium
- D-003 OpenCV 对比用 SSIM + 模板匹配双策略
- D-004 稳定性测试基于 Monkey + 自定义事件序列
- D-005 存储用 SQLite，截图文件系统化管理
