---
inclusion: auto
---
# 代码审查检查清单（Test_Auto 项目级）

## 通用检查（所有改动）

- [ ] 函数/类有 docstring
- [ ] 公开函数的参数和返回值有类型注解
- [ ] 没有裸 `except:`
- [ ] 没有用 `print` 输出，用 `logging`
- [ ] 没有硬编码绝对路径
- [ ] 单 commit 只做一件事
- [ ] kiro-log 已追加条目
- [ ] config.example.yaml 已同步（如有新增配置）

## 仓库管理（repo/）

- [ ] clone/pull 有超时设置
- [ ] 大仓库支持 shallow clone（--depth）
- [ ] 分支切换前检查 dirty 状态
- [ ] 错误信息包含仓库 URL 和分支名

## 代码分析（analyzer/）

- [ ] 不执行被分析的代码
- [ ] AST 解析失败有 graceful fallback
- [ ] 分析结果有缓存（避免重复解析）
- [ ] 支持增量分析（只分析变更文件）

## 测试生成（generator/）

- [ ] 生成的测试代码可直接编译运行
- [ ] 测试方法命名符合目标框架规范
- [ ] 不覆盖已有的手写测试
- [ ] 生成前检查目标目录是否存在

## 测试执行（runner/）

- [ ] 所有设备操作有超时
- [ ] 设备断连有重试机制
- [ ] 测试结果写入数据库
- [ ] 异常不会导致设备处于脏状态（app 未关闭等）

## OpenCV 对比（runner/opencv/）

- [ ] 截图前等待页面稳定（无动画）
- [ ] 对比阈值可配置
- [ ] 差异图保存到报告目录
- [ ] mask 区域正确排除动态内容

## 存储（storage/）

- [ ] 批量写入用事务
- [ ] schema 变更带 migration
- [ ] 截图文件路径用相对路径存储

## 提交前最后检查

- [ ] `git diff --staged` 确认无意外文件
- [ ] 没有提交：截图文件 / .db / data/ / configs/config.yaml
- [ ] commit message 符合规范
