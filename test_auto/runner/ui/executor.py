"""UI 自动化测试执行器 - 基于 uiautomator2."""

import logging
import time
from pathlib import Path
from typing import Optional

import uiautomator2 as u2

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10  # seconds


class UIRunnerError(Exception):
    """UI 测试执行异常."""


class UIRunner:
    """UI 自动化测试执行器."""

    def __init__(self, serial: Optional[str] = None, screenshots_dir: Optional[Path] = None) -> None:
        """初始化.

        Args:
            serial: 设备序列号，None 则连接第一个设备
            screenshots_dir: 截图保存目录
        """
        self._serial = serial
        self._device: Optional[u2.Device] = None
        self._screenshots_dir = screenshots_dir or Path("data/screenshots")
        self._screenshots_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> None:
        """连接设备."""
        try:
            if self._serial:
                self._device = u2.connect(self._serial)
            else:
                self._device = u2.connect()
            info = self._device.info
            logger.info("已连接设备: %s (Android %s)",
                        info.get("productName", "unknown"),
                        self._device.device_info.get("version", "unknown"))
        except Exception as e:
            raise UIRunnerError(f"设备连接失败: {e}") from e

    @property
    def device(self) -> u2.Device:
        """获取设备实例."""
        if self._device is None:
            raise UIRunnerError("设备未连接，请先调用 connect()")
        return self._device

    def launch_app(self, package_name: str) -> None:
        """启动应用.

        Args:
            package_name: 应用包名
        """
        self.device.app_start(package_name)
        time.sleep(2)  # 等待启动
        logger.info("已启动: %s", package_name)

    def stop_app(self, package_name: str) -> None:
        """停止应用."""
        self.device.app_stop(package_name)
        logger.info("已停止: %s", package_name)

    def take_screenshot(self, name: str) -> Path:
        """截图.

        Args:
            name: 截图名称（不含扩展名）

        Returns:
            截图文件路径
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        save_path = self._screenshots_dir / filename
        self.device.screenshot(str(save_path))
        logger.info("截图: %s", save_path)
        return save_path

    def click(self, text: Optional[str] = None, resource_id: Optional[str] = None,
              description: Optional[str] = None) -> bool:
        """点击元素.

        Args:
            text: 文本匹配
            resource_id: resource-id 匹配
            description: content-description 匹配

        Returns:
            是否点击成功
        """
        selector = self._build_selector(text=text, resource_id=resource_id, description=description)
        if selector.exists(timeout=_DEFAULT_TIMEOUT):
            selector.click()
            return True
        logger.warning("元素未找到: text=%s, id=%s", text, resource_id)
        return False

    def wait_for(self, text: Optional[str] = None, resource_id: Optional[str] = None,
                 timeout: int = _DEFAULT_TIMEOUT) -> bool:
        """等待元素出现.

        Args:
            text: 文本匹配
            resource_id: resource-id 匹配
            timeout: 超时秒数

        Returns:
            元素是否出现
        """
        selector = self._build_selector(text=text, resource_id=resource_id)
        return selector.exists(timeout=timeout)

    def swipe_up(self) -> None:
        """向上滑动."""
        self.device.swipe_ext("up", scale=0.8)

    def swipe_down(self) -> None:
        """向下滑动."""
        self.device.swipe_ext("down", scale=0.8)

    def get_current_activity(self) -> str:
        """获取当前 Activity."""
        info = self.device.app_current()
        return info.get("activity", "")

    def _build_selector(self, text: Optional[str] = None, resource_id: Optional[str] = None,
                        description: Optional[str] = None):
        """构建 UI 选择器."""
        if resource_id:
            return self.device(resourceId=resource_id)
        if text:
            return self.device(text=text)
        if description:
            return self.device(description=description)
        raise UIRunnerError("必须指定 text、resource_id 或 description 之一")
