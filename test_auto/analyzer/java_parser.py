"""Java AST 解析器 - 提取类/方法/依赖信息."""

import logging
from pathlib import Path
from typing import Optional

import javalang

from test_auto.models.schemas import ClassInfo, MethodInfo

logger = logging.getLogger(__name__)

# Android 常见基类映射
_ACTIVITY_BASES = {"Activity", "AppCompatActivity", "FragmentActivity", "BaseActivity"}
_FRAGMENT_BASES = {"Fragment", "DialogFragment", "BottomSheetDialogFragment"}


def parse_java_file(file_path: Path) -> Optional[ClassInfo]:
    """解析单个 Java 文件，提取主类信息.

    Args:
        file_path: Java 源文件路径

    Returns:
        ClassInfo 或 None（解析失败时）
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = javalang.parse.parse(source)
    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as e:
        logger.warning("解析失败 %s: %s", file_path.name, e)
        return None
    except Exception as e:
        logger.warning("未知解析错误 %s: %s", file_path.name, e)
        return None

    package = tree.package.name if tree.package else ""

    # 取第一个顶层类
    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        superclass = ""
        if node.extends:
            superclass = node.extends.name

        interfaces = []
        if node.implements:
            interfaces = [impl.name for impl in node.implements]

        methods = []
        for method in node.methods:
            methods.append(method.name)

        # 解析构造函数
        constructors = []
        if node.constructors:
            for ctor in node.constructors:
                params = []
                if ctor.parameters:
                    for p in ctor.parameters:
                        type_name = p.type.name if p.type else "Object"
                        params.append(f"{type_name} {p.name}")
                constructors.append(params)

        is_activity = superclass in _ACTIVITY_BASES
        is_fragment = superclass in _FRAGMENT_BASES

        return ClassInfo(
            name=node.name,
            package=package,
            file_path=str(file_path),
            superclass=superclass,
            interfaces=interfaces,
            methods=methods,
            constructors=constructors,
            is_abstract="abstract" in (node.modifiers or []),
            is_activity=is_activity,
            is_fragment=is_fragment,
        )

    return None


def parse_methods(file_path: Path) -> list[MethodInfo]:
    """解析文件中所有公开方法.

    Args:
        file_path: Java 源文件路径

    Returns:
        方法信息列表
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = javalang.parse.parse(source)
    except Exception as e:
        logger.warning("解析失败 %s: %s", file_path.name, e)
        return []

    results = []
    for _, cls_node in tree.filter(javalang.tree.ClassDeclaration):
        for method in cls_node.methods:
            params = []
            if method.parameters:
                for p in method.parameters:
                    type_name = p.type.name if p.type else "Object"
                    params.append(f"{type_name} {p.name}")

            return_type = "void"
            if method.return_type:
                return_type = method.return_type.name

            is_public = "public" in (method.modifiers or set())
            is_static = "static" in (method.modifiers or set())

            results.append(MethodInfo(
                name=method.name,
                class_name=cls_node.name,
                return_type=return_type,
                params=params,
                is_public=is_public,
                is_static=is_static,
                line_start=method.position.line if method.position else 0,
            ))

    return results
