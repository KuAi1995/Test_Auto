"""Android 资源文件分析 - 解析 attrs.xml 提取自定义属性."""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_ANDROID_NS = "http://schemas.android.com/apk/res/android"


@dataclass
class CustomAttr:
    """自定义属性."""

    name: str
    format: str = ""  # enum, color, dimension, reference, etc.
    enum_values: list[str] = field(default_factory=list)


@dataclass
class Styleable:
    """declare-styleable 定义."""

    name: str
    attrs: list[CustomAttr] = field(default_factory=list)


def parse_attrs_xml(attrs_path: Path) -> list[Styleable]:
    """解析 attrs.xml 提取 declare-styleable.

    Args:
        attrs_path: attrs.xml 路径

    Returns:
        Styleable 列表
    """
    if not attrs_path.exists():
        return []

    try:
        tree = ET.parse(attrs_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.warning("attrs.xml 解析失败: %s", e)
        return []

    styleables = []
    for ds in root.findall("declare-styleable"):
        name = ds.get("name", "")
        if not name:
            continue

        attrs = []
        for attr in ds.findall("attr"):
            attr_name = attr.get("name", "")
            attr_format = attr.get("format", "")

            enum_values = []
            for enum in attr.findall("enum"):
                enum_values.append(enum.get("name", ""))

            if attr_name:
                attrs.append(CustomAttr(name=attr_name, format=attr_format, enum_values=enum_values))

        styleables.append(Styleable(name=name, attrs=attrs))

    logger.info("解析 attrs.xml: %d styleables, %d attrs",
                len(styleables), sum(len(s.attrs) for s in styleables))
    return styleables


def find_attrs_files(project_path: Path) -> list[Path]:
    """查找项目中所有 attrs.xml."""
    candidates = list(project_path.rglob("attrs.xml"))
    return [c for c in candidates if "/build/" not in str(c) and "/values/" in str(c)]
