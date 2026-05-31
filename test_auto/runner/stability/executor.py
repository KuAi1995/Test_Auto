"""稳定性测试执行器 - Monkey + 自定义压力测试."""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ADB_TIMEOUT = 600  # 10 minutes for monkey


@dataclass
class StabilityResult:
    """稳定性测试结果."""

    events_injected: int = 0
    duration_seconds: float = 0
    crashes: list[str] = field(default_factory=list)
    anrs: list[str] = field(default_factory=list)
    success: bool = True
    log_path: Optional[str] = None

    @property
    def summary(self) -> str:
        return (
            f"事件: {self.events_injected}, 耗时: {self.duration_seconds:.1f}s, "
            f"崩溃: {len(self.crashes)}, ANR: {len(self.anrs)}, "
            f"结果: {'PASS' if self.success else 'FAIL'}"
        )


class StabilityRunner:
    """稳定性测试执行器."""

    def __init__(self, serial: Optional[str] = None, log_dir: Optional[Path] = None) -> None:
        self._serial = serial
        self._log_dir = log_dir or Path("data/logs/stability")
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def run_monkey(
        self,
        package_name: str,
        event_count: int = 5000,
        throttle_ms: int = 300,
        seed: Optional[int] = None,
        categories: Optional[list[str]] = None,
    ) -> StabilityResult:
        """执行 Monkey 测试.

        Args:
            package_name: 目标包名
            event_count: 事件数量
            throttle_ms: 事件间隔（毫秒）
            seed: 随机种子（可复现）
            categories: 限制的 intent category

        Returns:
            测试结果
        """
        cmd = ["adb"]
        if self._serial:
            cmd.extend(["-s", self._serial])

        cmd.extend(["shell", "monkey", "-p", package_name])

        if seed is not None:
            cmd.extend(["-s", str(seed)])
        if categories:
            for cat in categories:
                cmd.extend(["-c", cat])

        cmd.extend([
            "--throttle", str(throttle_ms),
            "--ignore-crashes",
            "--ignore-timeouts",
            "--ignore-security-exceptions",
            "-v", "-v",
            str(event_count),
        ])

        logger.info("执行 Monkey: %s, events=%d, throttle=%dms", package_name, event_count, throttle_ms)

        import time
        start = time.time()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=_ADB_TIMEOUT
            )
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = "TIMEOUT: Monkey 执行超时"
            logger.error("Monkey 执行超时 (%ds)", _ADB_TIMEOUT)

        duration = time.time() - start

        # 保存日志
        import time as t
        log_file = self._log_dir / f"monkey_{t.strftime('%Y%m%d_%H%M%S')}.log"
        log_file.write_text(output, encoding="utf-8")

        # 解析结果
        stability_result = self._parse_monkey_output(output)
        stability_result.duration_seconds = duration
        stability_result.log_path = str(log_file)

        logger.info("Monkey 完成: %s", stability_result.summary)
        return stability_result

    def _parse_monkey_output(self, output: str) -> StabilityResult:
        """解析 Monkey 输出."""
        result = StabilityResult()

        # 提取注入事件数
        match = re.search(r"Events injected: (\d+)", output)
        if match:
            result.events_injected = int(match.group(1))

        # 检测崩溃
        crashes = re.findall(r"// CRASH: (.+?) \(", output)
        result.crashes = crashes

        # 检测 ANR
        anrs = re.findall(r"// NOT RESPONDING: (.+?) \(", output)
        result.anrs = anrs

        # 判断成功
        result.success = len(crashes) == 0 and len(anrs) == 0

        return result
