# 进度

## 当前阶段：M1 基础设施（已完成）

### 已完成

#### M0 项目骨架
- [x] Git 仓库初始化 + GitHub remote
- [x] `.kiro/` 配置（steering + agents + sh）
- [x] `docs/` 文档骨架（architecture / progress / kiro-log）
- [x] kiro-agents 同步系统接入

#### M1 基础设施
- [x] Python 包结构搭建（config/utils/models）
- [x] 配置加载（Pydantic v2 + YAML）
- [x] ADB 工具封装（设备发现/连接/截图）
- [x] SQLite schema 设计 + migration
- [x] CLI 入口（init/devices/repo/analyze）
- [x] 数据模型定义（TestCase/TestResult/ClassInfo/MethodInfo）
- [x] repo 模块：clone/pull/status

### 待实现

#### M2 仓库管理 + 代码分析
- [x] analyzer：Java AST 解析（javalang）
- [x] analyzer：类/方法/依赖提取
- [ ] analyzer：类/方法/依赖提取
- [ ] analyzer：覆盖率分析接口

#### M3 单元测试生成
- [x] generator/unit：基于分析结果生成 JUnit 测试
- [x] 自动区分 Robolectric / 纯 JUnit
- [ ] 模板引擎（Jinja2）— 当前用字符串模板，够用
- [ ] 边界值 / 异常路径自动推断

#### M4 人工测试用例
- [x] generator/manual：结构化用例模板
- [ ] 用例 CRUD（SQLite 存储）
- [ ] 用例导入/导出（YAML/Excel）

#### M5 UI 自动化
- [x] runner/ui：uiautomator2 集成
- [ ] 页面对象模型（POM）
- [ ] 测试脚本录制/回放

#### M6 稳定性测试
- [x] runner/stability：Monkey 封装
- [ ] 自定义事件序列
- [ ] 崩溃/ANR 日志收集与分析

#### M7 OpenCV UI 对比
- [x] runner/opencv：SSIM 相似度计算
- [x] 差异区域标注 + mask 排除
- [ ] 基线管理（版本化）

#### M8 报告
- [x] reporter：HTML 报告模板
- [x] JSON 报告输出
- [ ] 测试趋势图表
- [ ] 失败用例截图嵌入

#### M9 GUI（可选）
- [ ] PySide6 主窗口
- [ ] 设备管理页
- [ ] 测试执行页
- [ ] 报告浏览页

## 模块状态

| 模块 | 状态 | 备注 |
|------|------|------|
| config | ✅ | Pydantic v2 + YAML |
| repo | ✅ | clone/pull/status |
| analyzer | ✅ | Java AST (javalang) |
| generator | 🟡 | unit 生成器完成 |
| runner | 🟡 | ui/stability/opencv 核心完成 |
| reporter | ✅ | HTML + JSON |
| storage | ✅ | SQLite schema v1 |
| utils | 🟡 | ADB 封装完成 |
| models | ✅ | 核心数据模型 |
| gui | ⬜ | 待实现 |
