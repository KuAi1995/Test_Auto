# Kiro Log

## 2026-05-31

### 项目初始化

- [决策] 项目定位：Android App 自动化测试平台，覆盖单元测试生成、人工用例、全路径自动化（稳定性 + OpenCV UI 对比）
- [决策] 核心流程：拉取远程仓库 → 代码分析 → 测试生成 → 测试执行 → 报告
- [决策] 模块划分：config / repo / analyzer / generator / runner / reporter / storage / utils
- [决策] 接入 kiro-agents 同步系统
- [待办] M2 仓库管理 + 代码分析

### 15:55 M1 基础设施搭建

- [已解决] M1 基础设施搭建完成
- [决策] 目标 App: git@github.com:KuAi1995/FUOS.git
- [决策] 配置系统: Pydantic v2 + YAML，配置模板 configs/config.example.yaml
- [决策] 存储: SQLite WAL 模式，schema v1（test_case/test_run/test_result/baseline_image）
- [决策] CLI 入口: python -m test_auto，子命令 init/devices/repo/analyze
- [决策] ADB 封装: subprocess + timeout，统一通过 utils/adb.py 调用
- [决策] pyproject.toml 指定 setuptools packages.find include=["test_auto*"] 避免 flat-layout 冲突

### 15:57 M2 代码分析器

- [已解决] Java AST 分析器实现完成
- [决策] 使用 javalang 库解析 Java AST（轻量，纯 Python，无需 tree-sitter 编译）
- [决策] 分析器跳过 build/ test/ androidTest/ 目录
- [决策] 自动识别 Activity/Fragment（基于继承关系）
- FUOS 项目分析结果：28 类、109 方法、4 包、10 Activity
- [待办] M3 单元测试生成器（基于分析结果）

### 15:59 M3 单元测试生成器

- [已解决] 单元测试生成器实现完成
- [决策] 自动区分 Robolectric（需 Context）和纯 JUnit 测试
- [决策] 跳过 Activity/Fragment（属于 UI 测试范畴）
- [决策] 为每个公开方法生成独立测试方法，参数用类型默认值
- FUOS 生成结果：15 个测试文件（9 widget + 6 utils）
- [待办] 已知限制：构造函数参数未被分析，SPUtils 等需要 Context 的类可能生成不完整的 setUp
- [待办] M4 人工测试用例模板生成

### 16:00 M4 人工测试用例生成器

- [已解决] 人工测试用例生成器实现完成
- [决策] Widget 类生成 UI 交互用例（渲染/状态切换/Disabled/点击）
- [决策] 工具类生成功能调用用例（每个公开方法一条）
- [决策] 输出格式 YAML，符合 dev-guidelines 中定义的用例模板
- FUOS 生成结果：76 条测试用例
- [待办] M5 UI 自动化测试执行器

### 16:03 M5-M8 测试执行层

- [已解决] UI 自动化执行器 (uiautomator2)
- [已解决] 稳定性测试执行器 (Monkey)
- [已解决] OpenCV UI 对比器 (SSIM + 差异标注)
- [已解决] HTML/JSON 报告生成器
- [决策] UI 对比使用 SSIM 算法，阈值默认 0.95
- [决策] 差异图拼接基线+标注实际图，红框标注差异区域
- [决策] Monkey 使用 --ignore-crashes/timeouts 持续执行，事后分析日志
- [决策] 报告同时输出 HTML（人读）和 JSON（程序读）
- [待办] 集成测试：连接真实设备验证完整流程

### 16:04 Pipeline 编排器

- [已解决] 完整流程编排器实现
- [决策] `python -m test_auto run` 一键执行: clone → 分析 → 生成 → 报告
- [决策] 支持 --skip-clone 跳过仓库同步（开发调试用）
- FUOS 完整流程验证通过：0.2s 完成分析+生成+报告
