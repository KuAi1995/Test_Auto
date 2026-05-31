# Test_Auto

Android App 自动化测试平台 —— 从代码分析到全路径自动化测试的一站式解决方案。

## 状态

🟡 **核心功能就绪**：M1-M8 完成，可执行完整流程。详见 [`docs/progress.md`](docs/progress.md)。

## 目标 App

- **FUOS** (`git@github.com:KuAi1995/FUOS.git`) — Android UI SDK

## 能力矩阵

| 测试类型 | 工具 | 状态 | 说明 |
|----------|------|------|------|
| 代码分析 | javalang (Java AST) | ✅ | 类/方法/继承/Activity 识别 |
| 单元测试生成 | JUnit / Robolectric | ✅ | 自动区分需 Context 的类 |
| 人工测试用例 | YAML 结构化模板 | ✅ | Widget 交互 + 工具类功能 |
| UI 自动化 | uiautomator2 | ✅ | 连接/启动/点击/截图/滑动 |
| 稳定性测试 | Monkey | ✅ | 事件注入/崩溃检测/日志解析 |
| UI 对比 | OpenCV (SSIM) | ✅ | 差异标注 + mask 排除 |
| 测试报告 | HTML + JSON | ✅ | 统计摘要 + 详细结果 |

## 核心流程

```
拉取远程仓库 → 代码静态分析 → 测试生成 → 测试执行 → 报告输出
```

## 快速开始

```bash
# 1. 安装依赖
pip install -e .

# 2. 复制配置模板
cp configs/config.example.yaml configs/config.yaml

# 3. 配置目标仓库
# 编辑 configs/config.yaml，填入仓库 URL

# 4. 初始化
python -m test_auto init

# 5. 一键执行完整流程
python -m test_auto run
```

## CLI 命令

```bash
python -m test_auto init                    # 初始化工作目录和数据库
python -m test_auto repo clone              # Clone 目标仓库
python -m test_auto repo pull               # Pull 最新代码
python -m test_auto analyze                 # 代码分析
python -m test_auto generate unit           # 生成单元测试
python -m test_auto generate manual         # 生成人工测试用例
python -m test_auto run                     # 执行完整流程
python -m test_auto run --skip-clone        # 跳过仓库同步
python -m test_auto devices                 # 列出已连接设备
```

## 目录结构

```
test_auto/
├── config/              配置加载 (Pydantic v2 + YAML)
├── repo/                远程仓库管理 (clone/pull/status)
├── analyzer/            代码静态分析 (Java AST)
├── generator/           测试生成器
│   ├── unit/            单元测试生成 (JUnit/Robolectric)
│   ├── manual/          人工测试用例 (YAML)
│   └── e2e/             E2E 脚本生成 (待实现)
├── runner/              测试执行引擎
│   ├── unit/            单元测试运行 (待实现)
│   ├── ui/              UI 自动化 (uiautomator2)
│   ├── stability/       稳定性测试 (Monkey)
│   └── opencv/          OpenCV UI 对比 (SSIM)
├── reporter/            测试报告 (HTML + JSON)
├── models/              数据模型 (Pydantic)
├── storage/             SQLite 存储
├── utils/               工具 (ADB)
├── pipeline.py          流程编排
└── __main__.py          CLI 入口
```

## FUOS 分析结果

```
类: 28, 方法: 109, 包: 4, Activity: 10
单元测试: 15 文件生成
人工用例: 76 条生成
```

## 开发

- 进度与待办：[`docs/progress.md`](docs/progress.md)
- 架构：[`docs/architecture.md`](docs/architecture.md)
- 开发日志：[`docs/kiro-log.md`](docs/kiro-log.md)

## 许可证

[LICENSE](LICENSE)
