---
inclusion: auto
---
# 项目级开发规范（Test_Auto）

继承系统级 `dev-guidelines.md`，本文件只记录项目专属约束。

## 1. 项目定位

Android App 自动化测试平台，覆盖：
- 远程仓库拉取 → 代码分析 → 单元测试生成
- 人工测试用例管理
- 全路径自动化测试（稳定性测试、OpenCV UI 对比）

## 2. 模块边界

```
config/              配置加载（YAML）
repo/                远程仓库管理（clone/pull/分支切换）
analyzer/            代码静态分析（AST 解析、依赖图、覆盖率分析）
generator/           测试生成器
  ├── unit/          单元测试生成（基于代码分析）
  ├── manual/        人工测试用例模板生成
  └── e2e/           全路径自动化测试脚本生成
runner/              测试执行引擎
  ├── unit/          单元测试运行（JUnit/Robolectric）
  ├── ui/            UI 自动化（uiautomator2/Appium）
  ├── stability/     稳定性测试（Monkey/自定义压力）
  └── opencv/        OpenCV UI 截图对比
reporter/            测试报告生成（HTML/JSON）
models/              数据模型（TestCase/TestResult/CoverageReport）
storage/             SQLite 存储（用例库/执行历史/基线截图）
utils/               工具（ADB/设备管理/截图/日志）
gui/                 PySide6 GUI（可选，后续）
```

边界铁则：
- `analyzer` 只做静态分析，不执行代码
- `generator` 只生成测试代码/用例，不执行
- `runner` 只负责执行和收集结果，不做分析
- 设备操作统一通过 `utils/adb.py`，其他模块不直接调 adb

## 3. 测试层级

| 层级 | 工具 | 目标 |
|------|------|------|
| 单元测试 | JUnit + Robolectric | 方法级覆盖 |
| 人工用例 | 结构化模板 | 业务流程验证 |
| UI 自动化 | uiautomator2 / Appium | 全路径回归 |
| 稳定性 | Monkey + 自定义脚本 | 崩溃/ANR 检测 |
| UI 对比 | OpenCV + 基线截图 | 视觉回归 |

## 4. 配置管理

- 配置文件：`configs/config.yaml`（实际，gitignore）+ `configs/config.example.yaml`（模板）
- 目标仓库：`repos.{name}.url` / `repos.{name}.branch`
- 设备配置：`devices.{serial}.name` / `devices.{serial}.platform_version`
- OpenCV 阈值：`opencv.similarity_threshold`（默认 0.95）
- 所有路径可配置，禁止硬编码

## 5. ADB / 设备管理

- 设备连接状态通过 `utils/adb.py` 统一管理
- 多设备并行测试时用设备池（device pool）分配
- 截图统一存储到 `data/screenshots/{device}/{timestamp}/`
- 设备断连自动重试 3 次，失败标记设备离线

## 6. OpenCV UI 对比规范

- 基线截图存储：`data/baselines/{app}/{version}/{screen_name}.png`
- 对比结果：差异图 + 相似度分数 + 差异区域标注
- 阈值可按页面独立配置（全局默认 0.95）
- 动态区域（时间/广告）通过 mask 排除

## 7. 测试用例格式

```yaml
# 人工测试用例模板
id: TC-{module}-{seq}
title: 用例标题
precondition: 前置条件
steps:
  - action: 操作描述
    expected: 预期结果
priority: P0/P1/P2/P3
module: 所属模块
automated: true/false
```

## 8. 存储规范

- SQLite 主表：`test_case` / `test_run` / `test_result` / `baseline_image`
- 执行历史按 run_id 关联
- 基线截图版本化管理（app_version + screen_name 为键）
