---
inclusion: auto
---
# 项目级经验沉淀（Test_Auto）

继承系统级 `~/.kiro/steering/self-evolving-rules.md`，本文件记录项目专属规则。

规则编号格式：`P-XXX`（项目级），与系统级 `R-XXX` 区分。

## 已沉淀规则

<!-- 暂无项目专属规则。首条规则将在实现核心功能时沉淀。 -->

## 待观察事项

- uiautomator2 在不同 Android 版本的兼容性差异
- OpenCV 模板匹配在不同分辨率设备上的阈值调优
- ADB 连接稳定性（WiFi vs USB）
- 大型仓库 clone 超时处理
- Robolectric 对 Android SDK 版本的支持范围

## 演进流程

参考系统级 `self-evolving-rules.md` 的提取时机和分层规则。
项目专属规则写在本文件，跨项目通用规则上提到系统级。
