---
inclusion: auto
---
# 项目级指令理解（Test_Auto）

继承系统级 `~/.kiro/steering/executor.md`，补充本项目专属映射。

## 项目专属指令映射

| 用户说 | 意图 | 执行动作 |
|--------|------|----------|
| 拉仓库 / clone | 拉取目标 Android 项目 | 调用 repo 模块 clone/pull |
| 分析代码 | 对目标仓库做静态分析 | 调用 analyzer 模块 |
| 生成单测 | 生成单元测试 | 调用 generator/unit |
| 生成用例 | 生成人工测试用例 | 调用 generator/manual |
| 跑测试 | 执行测试 | 根据上下文判断是 unit/ui/stability |
| 跑稳定性 | 执行稳定性测试 | 调用 runner/stability |
| 对比 UI / 截图对比 | OpenCV UI 对比 | 调用 runner/opencv |
| 看设备 | 查看已连接设备 | adb devices |
| 看报告 | 查看最近测试报告 | 打开 reporter 输出 |
| 更新基线 | 更新 OpenCV 基线截图 | 替换 baselines 目录对应截图 |

## 项目特殊上下文推断

- "目标项目/目标仓库" 指被测试的 Android App 仓库
- "基线" 指 OpenCV UI 对比的参考截图
- "覆盖率" 默认指代码覆盖率（单元测试）
- "回归" 默认指 UI 自动化回归测试
- "压力测试" 等同于稳定性测试

## 纠错记录

<!-- 格式：PE-XXX | 用户原话 | AI 错误理解 | 正确意图 | 日期 -->
