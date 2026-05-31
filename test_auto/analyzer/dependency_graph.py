"""依赖图分析 - 类之间的引用关系."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DependencyGraph:
    """依赖图."""

    # class_name -> set of imported/referenced class names
    edges: dict[str, set[str]] = field(default_factory=dict)

    @property
    def total_edges(self) -> int:
        return sum(len(v) for v in self.edges.values())

    def get_dependents(self, class_name: str) -> set[str]:
        """获取依赖指定类的所有类."""
        return {k for k, v in self.edges.items() if class_name in v}

    def get_dependencies(self, class_name: str) -> set[str]:
        """获取指定类依赖的所有类."""
        return self.edges.get(class_name, set())

    def get_most_depended(self, top_n: int = 10) -> list[tuple[str, int]]:
        """获取被依赖最多的类."""
        counts: dict[str, int] = {}
        for deps in self.edges.values():
            for d in deps:
                counts[d] = counts.get(d, 0) + 1
        return sorted(counts.items(), key=lambda x: -x[1])[:top_n]


def build_dependency_graph(project_path: Path) -> DependencyGraph:
    """构建项目依赖图.

    Args:
        project_path: 项目根目录

    Returns:
        依赖图
    """
    graph = DependencyGraph()
    java_files = list(project_path.rglob("*.java"))

    # 收集所有项目内类名
    project_classes = set()
    for f in java_files:
        rel = str(f.relative_to(project_path))
        if "/build/" in rel or "/test/" in rel:
            continue
        # 类名 = 文件名去掉 .java
        project_classes.add(f.stem)

    # 分析每个文件的 import 和引用
    for f in java_files:
        rel = str(f.relative_to(project_path))
        if "/build/" in rel or "/test/" in rel:
            continue

        class_name = f.stem
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        deps = set()
        # 从 import 语句提取
        for match in re.finditer(r"import\s+[\w.]+\.(\w+)\s*;", content):
            imported = match.group(1)
            if imported in project_classes and imported != class_name:
                deps.add(imported)

        # 从类型引用提取（字段、参数、返回值）
        for ref_class in project_classes:
            if ref_class == class_name:
                continue
            if re.search(rf"\b{ref_class}\b", content):
                deps.add(ref_class)

        if deps:
            graph.edges[class_name] = deps

    logger.info("依赖图: %d 个类, %d 条边", len(graph.edges), graph.total_edges)
    return graph
