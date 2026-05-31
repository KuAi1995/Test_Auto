"""E2E 测试脚本生成器 - 基于 Manifest Activity 列表生成 uiautomator2 遍历脚本."""

import logging
from pathlib import Path
from typing import Optional

from test_auto.analyzer.manifest_parser import ManifestInfo

logger = logging.getLogger(__name__)

_SCRIPT_TEMPLATE = '''"""E2E 自动化测试 - {title}

自动生成，基于 AndroidManifest.xml Activity 列表。
"""

import time
import uiautomator2 as u2


PACKAGE = "{package}"
ACTIVITIES = {activities}


def connect(serial=None):
    """连接设备."""
    d = u2.connect(serial) if serial else u2.connect()
    print(f"已连接: {{d.device_info.get('productName', 'unknown')}}")
    return d


def launch(d, activity=None):
    """启动应用."""
    if activity:
        d.app_start(PACKAGE, activity)
    else:
        d.app_start(PACKAGE)
    time.sleep(2)


def take_screenshot(d, name):
    """截图."""
    path = f"screenshots/{{name}}_{{int(time.time())}}.png"
    d.screenshot(path)
    print(f"  截图: {{path}}")
    return path


def test_activity_launch(d, activity_name, label):
    """测试单个 Activity 启动."""
    print(f"\\n[测试] {{label}} ({{activity_name}})")
    try:
        d.app_start(PACKAGE, activity_name)
        time.sleep(2)

        # 验证不崩溃
        current = d.app_current()
        if current.get("package") != PACKAGE:
            print(f"  ✗ 应用已退出 (当前: {{current.get('package')}})")
            return False

        take_screenshot(d, label.replace("/", "_").replace(" ", "_"))
        print(f"  ✓ 启动成功")
        return True
    except Exception as e:
        print(f"  ✗ 异常: {{e}}")
        return False


def test_scroll_and_interact(d):
    """在当前页面滑动并尝试交互."""
    try:
        # 向下滑动
        d.swipe_ext("up", scale=0.5)
        time.sleep(0.5)
        # 向上滑回
        d.swipe_ext("down", scale=0.5)
        time.sleep(0.5)
        return True
    except Exception:
        return False


def run_all(serial=None):
    """执行全部 E2E 测试."""
    import os
    os.makedirs("screenshots", exist_ok=True)

    d = connect(serial)
    results = []

    for activity in ACTIVITIES:
        name = activity["name"]
        label = activity.get("label", name)
        passed = test_activity_launch(d, name, label)
        if passed:
            test_scroll_and_interact(d)
        results.append({{"activity": name, "label": label, "passed": passed}})

    # 汇总
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\\n{{'='*50}}")
    print(f"E2E 结果: {{passed}}/{{total}} 通过")
    if passed < total:
        print("失败:")
        for r in results:
            if not r["passed"]:
                print(f"  ✗ {{r['label']}}")
    print(f"{{'='*50}}")

    d.app_stop(PACKAGE)
    return results


if __name__ == "__main__":
    import sys
    serial = sys.argv[1] if len(sys.argv) > 1 else None
    run_all(serial)
'''


class E2EGenerator:
    """E2E 测试脚本生成器."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def generate(self, manifest_info: ManifestInfo) -> Optional[Path]:
        """基于 Manifest 生成 E2E 遍历脚本.

        Args:
            manifest_info: AndroidManifest 解析结果

        Returns:
            生成的脚本路径
        """
        if not manifest_info or not manifest_info.activities:
            logger.warning("无 Activity 信息，跳过 E2E 生成")
            return None

        package = manifest_info.package
        activities = []
        for a in manifest_info.activities:
            full_name = a.name if "." in a.name else f".{a.name}"
            activities.append({"name": full_name, "label": a.label or a.name})

        content = _SCRIPT_TEMPLATE.format(
            title=f"{package} E2E 遍历测试",
            package=package,
            activities=repr(activities),
        )

        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self._output_dir / "test_e2e.py"
        output_file.write_text(content, encoding="utf-8")
        logger.info("E2E 脚本生成: %s (%d activities)", output_file, len(activities))
        return output_file
