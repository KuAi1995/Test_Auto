"""代码分析器 - 扫描项目并提取结构信息."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

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

    def analyze(self, incremental: bool = False) -> AnalysisResult:
        """执行分析.

        Args:
            incremental: 是否增量分析（只分析 git diff 变更文件）

        Returns:
            分析结果
        """
        if incremental:
            java_files = self._get_changed_files()
            if not java_files:
                logger.info("无变更文件，跳过增量分析")
                return AnalysisResult()
            logger.info("增量分析 %d 个变更文件", len(java_files))
        else:
            java_files = list(self._root.rglob("*.java"))
            logger.info("发现 %d 个 Java 文件", len(java_files))

        return self._analyze_files(java_files)

    def get_commit_hash(self) -> str:
        """获取当前 commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=self._root, timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def _get_changed_files(self) -> list[Path]:
        """获取 git diff 变更的 Java 文件."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "--", "*.java"],
                capture_output=True, text=True, cwd=self._root, timeout=10,
            )
            if result.returncode != 0:
                return []
            files = []
            for line in result.stdout.strip().splitlines():
                f = self._root / line
                if f.exists():
                    files.append(f)
            return files
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _analyze_files(self, java_files: list[Path]) -> AnalysisResult:
        """分析文件列表."""
        result = AnalysisResult()

        for f in java_files:
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
