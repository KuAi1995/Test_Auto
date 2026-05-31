---
inclusion: auto
---
# Kiro CLI 使用规范（Test_Auto 项目级）

## 启动方式
```bash
.kiro/sh/kiro-start.sh
```

## 进入对话后的首要动作
1. 读取 [`docs/kiro-log.md`](../../docs/kiro-log.md) 最近 3 个日期条目，恢复对话上下文
2. 检查未关闭的 `[问题]` 和 `[待办]` 标签，主动提醒用户
3. 阅读 [`docs/progress.md`](../../docs/progress.md) 了解当前进度与待办
4. 使用 `/model` 确认当前模型

## 项目特点（用于上下文恢复）
- Android App 自动化测试平台
- 核心流程：拉取远程仓库 → 代码分析 → 单元测试生成 → 人工用例 → 全路径自动化
- 测试类型：单元测试 / UI 自动化 / 稳定性测试 / OpenCV UI 对比
- 工具链：uiautomator2 / Appium / OpenCV / ADB / JUnit / Robolectric

## 对话规范
- 代码修改前先确认影响范围
- 每完成一个功能点立即 commit + push（参考 commit-conventions.md）
- 涉及设备操作的改动需标注测试设备型号和 Android 版本

## 自演进检查点（每次完成功能模块/修复 bug 后）
1. 本次踩坑可否提取为项目级规则？→ 写入 `self-evolving-rules.md`
2. 该规则是否跨项目通用？→ 上提到 `~/.kiro/steering/`
3. 是否有新检查项需要加入 review checklist？
