---
inclusion: auto
---
# Commit 规范（Test_Auto 项目级）

继承系统级 `dev-guidelines.md` 第 7 条，并补充本项目专属 scope。

## 格式
```
<type>(<scope>): <subject>

- <变更明细 1>
- <变更明细 2>
```

## type
- `feat` 新功能
- `fix` Bug 修复
- `refactor` 重构
- `docs` 文档
- `chore` 构建/工具/依赖
- `perf` 性能
- `test` 测试

## scope（项目专属模块名）

| scope | 对应模块 |
|-------|----------|
| `config` | configs/、config/ |
| `repo` | repo/ |
| `analyzer` | analyzer/ |
| `generator` | generator/ |
| `unit-gen` | generator/unit/ |
| `manual-gen` | generator/manual/ |
| `e2e-gen` | generator/e2e/ |
| `runner` | runner/ |
| `unit-run` | runner/unit/ |
| `ui-run` | runner/ui/ |
| `stability` | runner/stability/ |
| `opencv` | runner/opencv/ |
| `reporter` | reporter/ |
| `models` | models/ |
| `storage` | storage/ |
| `utils` | utils/ |
| `adb` | utils/adb.py |
| `gui` | gui/ |
| `kiro` | .kiro/ |
| `docs` | docs/、README.md |
| `deps` | requirements.txt、pyproject.toml |

## 模块 → 文档同步映射

| 修改模块 | 必须同步文档 |
|---------|-------------|
| `analyzer/` | `docs/modules/analyzer.md` |
| `generator/` | `docs/modules/generator.md` |
| `runner/` | `docs/modules/runner.md` |
| `storage/` | `docs/modules/storage.md` |
| `reporter/` | `docs/modules/reporter.md` |
| 新增配置项 | `configs/config.example.yaml` + `README.md` |
| 任何代码改动 | `docs/kiro-log.md` 追加条目 |

## 提交前自查（强制）

1. 是否只做了一件事？
2. 文档/kiro-log 是否一起更新了？
3. 是否有测试截图/数据库文件被意外 staged？
4. `git status` 是否有意外文件？
