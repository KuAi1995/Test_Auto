"""代码分析器 - 扫描项目并提取结构信息."""

import logging
from pathlib import Path

from test_auto.analyzer.java_parser import parse_java_file, parse_methods
from test_auto.models.schemas import ClassInfo, MethodInfo

logger = logging.getLogger(__name__)


class AnalysisResult:
    """分析结果."""

    def __init__(self) -> None:
        self.classes: list[ClassInfo] = []
        self.methods: list[MethodInfo] = []
        self.packages: set[str] = set()
        self.activities: list[ClassInfo] = []
        self.fragments: list[ClassInfo] = []

    @property
    def total_classes(self) -> int:
        return len(self.classes)

    @property
    def total_methods(self) -> int:
        return len(self.methods)

    def summary(self) -> str:
        """生成分析摘要."""
        return (
            f"类: {self.total_classes}, 方法: {self.total_methods}, "
            f"包: {len(self.packages)}, "
            f"Activity: {len(self.activities)}, Fragment: {len(self.fragments)}"
        )


class Analyzer:
    """项目代码分析器."""

    def __init__(self, project_path: Path) -> None:
        """初始化分析器.

        Args:
            project_path: 项目根目录
        """
        self._root = project_path

    def analyze(self) -> AnalysisResult:
        """执行全量分析.

        Returns:
            分析结果
        """
        result = AnalysisResult()
        java_files = list(self._root.rglob("*.java"))
        logger.info("发现 %d 个 Java 文件", len(java_files))

        for f in java_files:
            # 跳过 build 目录和测试目录
            rel = str(f.relative_to(self._root))
            if "/build/" in rel or "/test/" in rel or "/androidTest/" in rel:
                continue

            class_info = parse_java_file(f)
            if class_info:
                result.classes.append(class_info)
                result.packages.add(class_info.package)
                if class_info.is_activity:
                    result.activities.append(class_info)
                if class_info.is_fragment:
                    result.fragments.append(class_info)

            methods = parse_methods(f)
            result.methods.extend(methods)

        logger.info("分析完成: %s", result.summary())
        return result
