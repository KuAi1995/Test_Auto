"""ADB 工具封装 - 设备发现/连接/截图."""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ADB_TIMEOUT = 30  # seconds


@dataclass
class Device:
    """已连接设备."""

    serial: str
    state: str  # device / offline / unauthorized
    model: str = ""
    android_version: str = ""


class ADBError(Exception):
    """ADB 操作异常."""


def _run_adb(args: list[str], serial: Optional[str] = None, timeout: int = _ADB_TIMEOUT) -> str:
    """执行 adb 命令.

    Args:
        args: adb 子命令参数
        serial: 指定设备序列号
        timeout: 超时秒数

    Returns:
        stdout 输出

    Raises:
        ADBError: 命令执行失败
    """
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise ADBError(f"adb {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired as e:
        raise ADBError(f"adb {' '.join(args)} timeout ({timeout}s)") from e
    except FileNotFoundError as e:
        raise ADBError("adb not found in PATH") from e


def list_devices() -> list[Device]:
    """列出所有已连接设备.

    Returns:
        设备列表
    """
    output = _run_adb(["devices", "-l"])
    devices = []
    for line in output.splitlines()[1:]:  # skip header
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            serial = parts[0]
            state = parts[1]
            model = ""
            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part.split(":", 1)[1]
            devices.append(Device(serial=serial, state=state, model=model))
    return devices


def get_device_prop(serial: str, prop: str) -> str:
    """获取设备属性.

    Args:
        serial: 设备序列号
        prop: 属性名 (如 ro.build.version.release)

    Returns:
        属性值
    """
    return _run_adb(["shell", "getprop", prop], serial=serial)


def screenshot(serial: str, save_path: Path) -> Path:
    """截取设备屏幕.

    Args:
        serial: 设备序列号
        save_path: 保存路径

    Returns:
        截图文件路径
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    remote_path = "/sdcard/test_auto_screenshot.png"
    _run_adb(["shell", "screencap", "-p", remote_path], serial=serial)
    _run_adb(["pull", remote_path, str(save_path)], serial=serial)
    _run_adb(["shell", "rm", remote_path], serial=serial)
    logger.info("截图已保存: %s", save_path)
    return save_path


def install_apk(serial: str, apk_path: Path) -> None:
    """安装 APK.

    Args:
        serial: 设备序列号
        apk_path: APK 文件路径
    """
    _run_adb(["install", "-r", str(apk_path)], serial=serial, timeout=120)
    logger.info("APK 已安装: %s", apk_path.name)
