"""人工测试用例生成器 - 基于代码分析生成结构化测试用例模板."""

import logging
from pathlib import Path

import yaml

from test_auto.models.schemas import ClassInfo, MethodInfo, TestPriority

logger = logging.getLogger(__name__)


def _generate_widget_cases(cls: ClassInfo, methods: list[MethodInfo]) -> list[dict]:
    """为 Widget 类生成 UI 测试用例."""
    cases = []
    seq = 1

    # 基础渲染测试
    cases.append({
        "id": f"TC-{cls.name}-{seq:03d}",
        "title": f"{cls.name} 基础渲染",
        "module": cls.name,
        "priority": TestPriority.P0.value,
        "precondition": f"打开包含 {cls.name} 的页面",
        "steps": [
            {"action": f"观察 {cls.name} 组件", "expected": "组件正常显示，无崩溃"},
        ],
        "automated": False,
    })
    seq += 1

    # 状态切换测试
    state_methods = [m for m in methods if m.name.startswith("set") and m.is_public]
    for m in state_methods:
        prop_name = m.name[3:]  # remove "set"
        cases.append({
            "id": f"TC-{cls.name}-{seq:03d}",
            "title": f"{cls.name} {prop_name} 状态切换",
            "module": cls.name,
            "priority": TestPriority.P1.value,
            "precondition": f"{cls.name} 已正常显示",
            "steps": [
                {"action": f"调用 {m.name} 切换状态", "expected": f"{prop_name} 状态正确变化"},
            ],
            "automated": False,
        })
        seq += 1

    # Enabled/Disabled 测试
    cases.append({
        "id": f"TC-{cls.name}-{seq:03d}",
        "title": f"{cls.name} Disabled 态",
        "module": cls.name,
        "priority": TestPriority.P1.value,
        "precondition": f"{cls.name} 已正常显示",
        "steps": [
            {"action": "设置 enabled=false", "expected": "组件变为不可用态（alpha 降低）"},
            {"action": "尝试点击组件", "expected": "无响应"},
        ],
        "automated": False,
    })
    seq += 1

    # 交互测试
    cases.append({
        "id": f"TC-{cls.name}-{seq:03d}",
        "title": f"{cls.name} 点击交互",
        "module": cls.name,
        "priority": TestPriority.P0.value,
        "precondition": f"{cls.name} 已正常显示且 enabled=true",
        "steps": [
            {"action": "点击组件", "expected": "有按压反馈（ripple/缩放/alpha 变化）"},
            {"action": "松开", "expected": "恢复正常态"},
        ],
        "automated": False,
    })

    return cases


def _generate_utils_cases(cls: ClassInfo, methods: list[MethodInfo]) -> list[dict]:
    """为工具类生成功能测试用例."""
    cases = []
    seq = 1

    for m in methods:
        if not m.is_public:
            continue
        cases.append({
            "id": f"TC-{cls.name}-{seq:03d}",
            "title": f"{cls.name}.{m.name} 正常调用",
            "module": cls.name,
            "priority": TestPriority.P1.value,
            "precondition": "App 正常运行",
            "steps": [
                {"action": f"调用 {cls.name}.{m.name}()", "expected": "返回正确结果，无异常"},
            ],
            "automated": True,
        })
        seq += 1

    return cases


class ManualTestGenerator:
    """人工测试用例生成器."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def generate_for_project(self, classes: list[ClassInfo], methods: list[MethodInfo]) -> Path:
        """为项目生成测试用例集.

        Args:
            classes: 类信息列表
            methods: 方法信息列表

        Returns:
            输出文件路径
        """
        all_cases = []

        for cls in classes:
            cls_methods = [m for m in methods if m.class_name == cls.name]

            if cls.is_activity or cls.is_fragment:
                continue  # Activity 的用例由 E2E 生成器处理

            # 判断是 Widget 还是工具类
            is_widget = cls.superclass in ("View", "FrameLayout", "LinearLayout", "RelativeLayout",
                                           "AppCompatButton", "AppCompatTextView", "AppCompatEditText")
            if is_widget:
                cases = _generate_widget_cases(cls, cls_methods)
            else:
                cases = _generate_utils_cases(cls, cls_methods)

            all_cases.extend(cases)

        # 输出 YAML
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self._output_dir / "test_cases.yaml"
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(all_cases, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info("生成 %d 条测试用例 → %s", len(all_cases), output_file)
        return output_file
