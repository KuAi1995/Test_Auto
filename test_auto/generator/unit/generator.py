"""单元测试生成器 - 基于代码分析结果生成 JUnit 测试."""

import logging
from pathlib import Path
from typing import Optional

from test_auto.analyzer.java_parser import parse_java_file, parse_methods
from test_auto.models.schemas import ClassInfo, MethodInfo

logger = logging.getLogger(__name__)

# Robolectric 测试模板（需要 Android Context 的类）
_ROBOLECTRIC_TEMPLATE = '''package {test_package};

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import android.content.Context;

import static org.junit.Assert.*;

import {full_class_name};

@RunWith(RobolectricTestRunner.class)
public class {class_name}Test {{

    private Context context;
{instance_field}
    @Before
    public void setUp() {{
        context = RuntimeEnvironment.getApplication();
{setup_code}    }}
{test_methods}}}
'''

# 纯 JUnit 测试模板（工具类/无 Android 依赖）
_JUNIT_TEMPLATE = '''package {test_package};

import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;

import {full_class_name};

public class {class_name}Test {{
{instance_field}
    @Before
    public void setUp() {{
{setup_code}    }}
{test_methods}}}
'''

# 需要 Context 的参数类型
_CONTEXT_TYPES = {"Context", "Activity", "Application", "Fragment"}


def _needs_context(methods: list[MethodInfo], class_info: Optional[ClassInfo] = None) -> bool:
    """判断类是否需要 Android Context."""
    # 检查构造函数参数
    if class_info and class_info.constructors:
        for ctor_params in class_info.constructors:
            for p in ctor_params:
                for ct in _CONTEXT_TYPES:
                    if ct in p:
                        return True
    # 检查方法参数
    for m in methods:
        for p in m.params:
            for ct in _CONTEXT_TYPES:
                if ct in p:
                    return True
    return False


def _generate_test_method(method: MethodInfo, class_name: str, needs_ctx: bool) -> str:
    """生成单个测试方法."""
    test_name = f"test{method.name[0].upper()}{method.name[1:]}"

    # 构建参数
    args = []
    for p in method.params:
        parts = p.split()
        if len(parts) >= 2:
            type_name = parts[0]
            args.append(_default_value(type_name, needs_ctx))

    args_str = ", ".join(args)

    if method.is_static:
        call = f"{class_name}.{method.name}({args_str})"
    else:
        call = f"instance.{method.name}({args_str})"

    if method.return_type == "void":
        body = f"        {call};\n        // 验证无异常抛出"
    elif method.return_type in ("int", "long", "float", "double"):
        body = f"        {method.return_type} result = {call};\n        assertTrue(result >= 0);"
    elif method.return_type == "boolean":
        body = f"        boolean result = {call};\n        assertNotNull(result);"
    else:
        body = f"        {_java_type(method.return_type)} result = {call};\n        assertNotNull(result);"

    # 生成主测试 + 边界值测试
    tests = f'''
    @Test
    public void {test_name}() {{
{body}
    }}
'''

    # 为有参数的方法生成 null/边界值测试
    boundary_test = _generate_boundary_test(method, class_name, needs_ctx)
    if boundary_test:
        tests += boundary_test

    return tests


def _generate_boundary_test(method: MethodInfo, class_name: str, needs_ctx: bool) -> str:
    """生成边界值/异常路径测试."""
    # 找到可以传 null 的参数（非基本类型、非 Context）
    nullable_params = []
    for i, p in enumerate(method.params):
        parts = p.split()
        if len(parts) >= 2:
            type_name = parts[0]
            if type_name not in ("int", "long", "float", "double", "boolean", "char", "byte", "short") \
               and type_name not in _CONTEXT_TYPES:
                nullable_params.append((i, type_name, parts[1]))

    if not nullable_params:
        return ""

    # 生成 null 参数测试
    test_name = f"test{method.name[0].upper()}{method.name[1:]}_nullParam"
    args = []
    for p in method.params:
        parts = p.split()
        if len(parts) >= 2:
            type_name = parts[0]
            args.append(_default_value(type_name, needs_ctx))

    # 将第一个可 null 参数设为 null
    idx = nullable_params[0][0]
    args[idx] = "null"
    args_str = ", ".join(args)

    if method.is_static:
        call = f"{class_name}.{method.name}({args_str})"
    else:
        call = f"instance.{method.name}({args_str})"

    return f'''
    @Test
    public void {test_name}() {{
        try {{
            {call};
        }} catch (NullPointerException | IllegalArgumentException e) {{
            // 预期异常
        }}
    }}
'''


def _default_value(type_name: str, needs_ctx: bool) -> str:
    """生成参数默认值."""
    if type_name in _CONTEXT_TYPES:
        return "context"
    defaults = {
        "String": '"test"',
        "int": "0",
        "long": "0L",
        "float": "0f",
        "double": "0.0",
        "boolean": "false",
        "char": "'a'",
    }
    return defaults.get(type_name, "null")


def _java_type(return_type: str) -> str:
    """返回类型（用于变量声明）."""
    primitives = {"int", "long", "float", "double", "boolean", "char", "byte", "short"}
    if return_type in primitives:
        return return_type
    return return_type


class UnitTestGenerator:
    """单元测试生成器."""

    def __init__(self, output_dir: Path) -> None:
        """初始化.

        Args:
            output_dir: 测试文件输出目录
        """
        self._output_dir = output_dir

    def generate_for_class(self, class_info: ClassInfo, methods: list[MethodInfo]) -> Optional[Path]:
        """为单个类生成测试文件.

        Args:
            class_info: 类信息
            methods: 该类的方法列表

        Returns:
            生成的测试文件路径，跳过时返回 None
        """
        # 跳过 Activity/Fragment（需要 UI 测试而非单元测试）
        if class_info.is_activity or class_info.is_fragment:
            logger.debug("跳过 Activity/Fragment: %s", class_info.name)
            return None

        # 只测试有公开方法的类
        public_methods = [m for m in methods if m.is_public and m.class_name == class_info.name]
        if not public_methods:
            return None

        needs_ctx = _needs_context(public_methods, class_info)
        test_package = class_info.package
        full_class_name = f"{class_info.package}.{class_info.name}"

        # 生成实例字段和 setup
        has_static_only = all(m.is_static for m in public_methods)
        instance_field = ""
        setup_code = ""
        if not has_static_only:
            instance_field = f"    private {class_info.name} instance;\n"
            # 根据构造函数参数生成正确的实例化代码
            ctor_args = self._build_ctor_args(class_info, needs_ctx)
            setup_code = f"        instance = new {class_info.name}({ctor_args});\n"

        # 生成测试方法
        test_methods = ""
        for m in public_methods:
            test_methods += _generate_test_method(m, class_info.name, needs_ctx)

        # 选择模板
        template = _ROBOLECTRIC_TEMPLATE if needs_ctx else _JUNIT_TEMPLATE
        content = template.format(
            test_package=test_package,
            full_class_name=full_class_name,
            class_name=class_info.name,
            instance_field=instance_field,
            setup_code=setup_code,
            test_methods=test_methods,
        )

        # 写入文件
        package_path = test_package.replace(".", "/")
        output_file = self._output_dir / package_path / f"{class_info.name}Test.java"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")
        logger.info("生成测试: %s", output_file.relative_to(self._output_dir))
        return output_file

    def _build_ctor_args(self, class_info: ClassInfo, needs_ctx: bool) -> str:
        """根据构造函数参数生成实例化参数."""
        if not class_info.constructors:
            # 无显式构造函数，View 子类默认需要 Context
            if needs_ctx:
                return "context"
            return ""

        # 选择参数最少的构造函数
        shortest = min(class_info.constructors, key=len)
        args = []
        for p in shortest:
            parts = p.split()
            if len(parts) >= 2:
                type_name = parts[0]
                args.append(_default_value(type_name, needs_ctx))
        return ", ".join(args)

    def generate_for_project(self, classes: list[ClassInfo], methods: list[MethodInfo]) -> list[Path]:
        """为整个项目生成测试.

        Args:
            classes: 所有类信息
            methods: 所有方法信息

        Returns:
            生成的测试文件路径列表
        """
        generated = []
        for cls in classes:
            cls_methods = [m for m in methods if m.class_name == cls.name]
            result = self.generate_for_class(cls, cls_methods)
            if result:
                generated.append(result)

        logger.info("共生成 %d 个测试文件", len(generated))
        return generated
