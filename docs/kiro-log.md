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
