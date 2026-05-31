"""AndroidManifest.xml 解析器 - 提取包名/Activity/权限."""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ANDROID_NS = "http://schemas.android.com/apk/res/android"


@dataclass
class ActivityEntry:
    """Manifest 中的 Activity 条目."""

    name: str  # 类名（可能是相对路径如 .MainActivity）
    label: str = ""
    exported: bool = False
    is_launcher: bool = False
    intent_actions: list[str] = field(default_factory=list)


@dataclass
class ManifestInfo:
    """AndroidManifest 解析结果."""

    package: str = ""
    activities: list[ActivityEntry] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    min_sdk: int = 0
    target_sdk: int = 0
    app_label: str = ""
    app_theme: str = ""

    @property
    def launcher_activity(self) -> Optional[str]:
        """获取启动 Activity 全限定名."""
        for a in self.activities:
            if a.is_launcher:
                return self._resolve_name(a.name)
        return None

    def _resolve_name(self, name: str) -> str:
        """解析相对类名为全限定名."""
        if name.startswith("."):
            return self.package + name
        if "." not in name:
            return f"{self.package}.{name}"
        return name

    def get_full_activity_names(self) -> list[str]:
        """获取所有 Activity 全限定名."""
        return [self._resolve_name(a.name) for a in self.activities]


def parse_manifest(manifest_path: Path) -> Optional[ManifestInfo]:
    """解析 AndroidManifest.xml.

    Args:
        manifest_path: manifest 文件路径

    Returns:
        ManifestInfo 或 None
    """
    if not manifest_path.exists():
        logger.warning("Manifest 不存在: %s", manifest_path)
        return None

    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.warning("Manifest 解析失败: %s", e)
        return None

    info = ManifestInfo()
    info.package = root.get("package", "")

    # AGP 8+ 不在 manifest 中声明 package，从 build.gradle namespace 读取
    if not info.package:
        info.package = _resolve_package_from_gradle(manifest_path)

    # 解析 uses-sdk
    uses_sdk = root.find("uses-sdk")
    if uses_sdk is not None:
        info.min_sdk = int(uses_sdk.get(f"{{{_ANDROID_NS}}}minSdkVersion", "0"))
        info.target_sdk = int(uses_sdk.get(f"{{{_ANDROID_NS}}}targetSdkVersion", "0"))

    # 解析权限
    for perm in root.findall("uses-permission"):
        name = perm.get(f"{{{_ANDROID_NS}}}name", "")
        if name:
            info.permissions.append(name)

    # 解析 application
    app = root.find("application")
    if app is not None:
        info.app_label = app.get(f"{{{_ANDROID_NS}}}label", "")
        info.app_theme = app.get(f"{{{_ANDROID_NS}}}theme", "")

        # 解析 activities
        for activity in app.findall("activity"):
            name = activity.get(f"{{{_ANDROID_NS}}}name", "")
            if not name:
                continue

            entry = ActivityEntry(
                name=name,
                label=activity.get(f"{{{_ANDROID_NS}}}label", ""),
                exported=activity.get(f"{{{_ANDROID_NS}}}exported", "false") == "true",
            )

            # 解析 intent-filter
            for intent_filter in activity.findall("intent-filter"):
                for action in intent_filter.findall("action"):
                    action_name = action.get(f"{{{_ANDROID_NS}}}name", "")
                    entry.intent_actions.append(action_name)
                for category in intent_filter.findall("category"):
                    cat_name = category.get(f"{{{_ANDROID_NS}}}name", "")
                    if cat_name == "android.intent.category.LAUNCHER":
                        entry.is_launcher = True

            info.activities.append(entry)

    logger.info("Manifest 解析: package=%s, activities=%d, permissions=%d",
                info.package, len(info.activities), len(info.permissions))
    return info


def find_manifest(project_path: Path) -> Optional[Path]:
    """在项目中查找主 AndroidManifest.xml（优先 app/demo 模块）.

    Args:
        project_path: 项目根目录

    Returns:
        manifest 路径
    """
    # 优先查找 app 或 demo 模块（有 launcher activity 的）
    candidates = list(project_path.rglob("AndroidManifest.xml"))
    # 排除 build 目录
    candidates = [c for c in candidates if "/build/" not in str(c)]

    for c in candidates:
        content = c.read_text(encoding="utf-8")
        if "android.intent.category.LAUNCHER" in content:
            return c

    return candidates[0] if candidates else None


def _resolve_package_from_gradle(manifest_path: Path) -> str:
    """从 build.gradle 的 namespace 读取包名（AGP 8+ 不在 manifest 中声明 package）."""
    import re
    # 向上找 build.gradle
    module_dir = manifest_path.parent
    while module_dir != module_dir.parent:
        for name in ("build.gradle", "build.gradle.kts"):
            gradle = module_dir / name
            if gradle.exists():
                content = gradle.read_text(encoding="utf-8")
                match = re.search(r'namespace\s+["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
                match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        module_dir = module_dir.parent
    return ""
