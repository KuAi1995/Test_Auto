# Test_Auto

Android App 自动化测试平台 —— 从代码分析到全路径自动化测试的一站式解决方案。

## 状态

🚧 **开发中**：M0 骨架就位。详见 [`docs/progress.md`](docs/progress.md)。

## 目标能力

| 测试类型 | 工具 | 说明 |
|----------|------|------|
| 单元测试生成 | JUnit / Robolectric | 基于代码分析自动生成 |
| 人工测试用例 | 结构化模板 | 业务流程验证 |
| UI 自动化 | uiautomator2 / Appium | 全路径回归测试 |
| 稳定性测试 | Monkey + 自定义脚本 | 崩溃/ANR 检测 |
| UI 对比 | OpenCV (SSIM) | 视觉回归测试 |

## 核心流程

```
拉取远程仓库 → 代码静态分析 → 测试生成 → 测试执行 → 报告输出
```

## 目录结构

```
test_auto/
├── config/              配置加载
├── repo/                远程仓库管理
├── analyzer/            代码静态分析
├── generator/           测试生成器
│   ├── unit/            单元测试生成
│   ├── manual/          人工测试用例
│   └── e2e/             E2E 脚本生成
├── runner/              测试执行引擎
│   ├── unit/            单元测试运行
│   ├── ui/              UI 自动化
│   ├── stability/       稳定性测试
│   └── opencv/          OpenCV UI 对比
├── reporter/            测试报告
├── models/              数据模型
├── storage/             SQLite + 截图存储
├── utils/               工具（ADB/设备管理）
├── gui/                 PySide6 GUI（可选）
├── configs/             配置文件
├── data/                运行数据（gitignore）
└── docs/                文档
```

## 快速开始（暂不可用，骨架阶段）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 复制配置模板
cp configs/config.example.yaml configs/config.yaml

# 3. 配置目标仓库和设备
$EDITOR configs/config.yaml

# 4. 运行
python -m test_auto <repo_url>
```

## 开发

- 启动 Kiro 开发会话：`.kiro/sh/kiro-start.sh`
- 进度与待办：[`docs/progress.md`](docs/progress.md)
- 架构：[`docs/architecture.md`](docs/architecture.md)

## 许可证

[LICENSE](LICENSE)
