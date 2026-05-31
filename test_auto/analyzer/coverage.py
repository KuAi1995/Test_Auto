"""覆盖率分析 - 对比已生成测试 vs 全部方法."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from test_auto.models.schemas import ClassInfo, MethodInfo

logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """覆盖率报告."""

    total_classes: int = 0
    tested_classes: int = 0
    total_methods: int = 0
    tested_methods: int = 0
    untested_classes: list[str] = field(default_factory=list)
    untested_methods: list[str] = field(default_factory=list)

    @property
    def class_coverage(self) -> float:
        """类覆盖率."""
        return self.tested_classes / self.total_classes if self.total_classes else 0

    @property
    def method_coverage(self) -> float:
        """方法覆盖率."""
        return self.tested_methods / self.total_methods if self.total_methods else 0

    def summary(self) -> str:
        return (
            f"类覆盖: {self.tested_classes}/{self.total_classes} ({self.class_coverage:.0%}), "
            f"方法覆盖: {self.tested_methods}/{self.total_methods} ({self.method_coverage:.0%})"
        )


def analyze_coverage(classes: list[ClassInfo], methods: list[MethodInfo],
                     test_output_dir: Path) -> CoverageReport:
    """分析测试覆盖率.

    Args:
        classes: 所有类信息
        methods: 所有方法信息
        test_output_dir: 生成的测试文件目录

    Returns:
        覆盖率报告
    """
    report = CoverageReport()

    # 统计可测试的类（排除 Activity/Fragment/抽象类）
    testable_classes = [c for c in classes if not c.is_activity and not c.is_fragment and not c.is_abstract]
    report.total_classes = len(testable_classes)

    # 统计可测试的公开方法
    testable_methods = [m for m in methods if m.is_public and
                        any(m.class_name == c.name for c in testable_classes)]
    report.total_methods = len(testable_methods)

    # 检查哪些类有对应的测试文件
    tested_class_names = set()
    if test_output_dir.exists():
        for test_file in test_output_dir.rglob("*Test.java"):
            class_name = test_file.stem.replace("Test", "")
            tested_class_names.add(class_name)

    for cls in testable_classes:
        if cls.name in tested_class_names:
            report.tested_classes += 1
            # 该类的所有公开方法视为已覆盖
            cls_methods = [m for m in testable_methods if m.class_name == cls.name]
            report.tested_methods += len(cls_methods)
        else:
            report.untested_classes.append(f"{cls.package}.{cls.name}")

    # 未覆盖的方法
    for m in testable_methods:
        if m.class_name not in tested_class_names:
            report.untested_methods.append(f"{m.class_name}.{m.name}")

    logger.info("覆盖率: %s", report.summary())
    return report
