"""崩溃日志分析器 - 从 logcat 提取 crash/ANR 信息."""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CrashInfo:
    """崩溃信息."""

    exception_type: str = ""
    message: str = ""
    stack_trace: str = ""
    process: str = ""
    timestamp: str = ""
    related_class: str = ""  # 关联到项目中的类


def collect_logcat(serial: Optional[str] = None, lines: int = 5000) -> str:
    """收集 logcat 日志.

    Args:
        serial: 设备序列号
        lines: 最近 N 行

    Returns:
        logcat 输出
    """
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["logcat", "-d", "-t", str(lines)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def parse_crashes(logcat_output: str, package_filter: str = "") -> list[CrashInfo]:
    """从 logcat 输出中解析崩溃信息.

    Args:
        logcat_output: logcat 文本
        package_filter: 只保留包含此包名的崩溃

    Returns:
        崩溃信息列表
    """
    crashes = []
    lines = logcat_output.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检测 FATAL EXCEPTION
        if "FATAL EXCEPTION" in line:
            crash = CrashInfo()
            crash.timestamp = line[:18] if len(line) > 18 else ""

            # 提取进程名
            proc_match = re.search(r"Process: ([^\s,]+)", lines[i + 1] if i + 1 < len(lines) else "")
            if proc_match:
                crash.process = proc_match.group(1)

            # 收集 stack trace
            stack_lines = []
            j = i + 1
            while j < len(lines) and j < i + 50:
                stack_lines.append(lines[j])
                # 检测异常类型
                exc_match = re.match(r".*?([a-zA-Z.]+Exception|[a-zA-Z.]+Error): (.+)", lines[j])
                if exc_match and not crash.exception_type:
                    crash.exception_type = exc_match.group(1)
                    crash.message = exc_match.group(2)
                # 检测 "at" 行中的项目类
                if package_filter and package_filter in lines[j] and "at " in lines[j]:
                    at_match = re.search(r"at ([^\(]+)\(", lines[j])
                    if at_match and not crash.related_class:
                        crash.related_class = at_match.group(1)
                if j > i + 2 and not lines[j].strip().startswith("at ") and "Caused by" not in lines[j]:
                    break
                j += 1

            crash.stack_trace = "\n".join(stack_lines[:30])

            if not package_filter or package_filter in crash.stack_trace or package_filter in crash.process:
                crashes.append(crash)
            i = j
        else:
            i += 1

    return crashes


def parse_anrs(logcat_output: str, package_filter: str = "") -> list[CrashInfo]:
    """从 logcat 中解析 ANR 信息."""
    anrs = []
    lines = logcat_output.splitlines()

    for i, line in enumerate(lines):
        if "ANR in" in line:
            anr = CrashInfo()
            anr.exception_type = "ANR"
            match = re.search(r"ANR in ([^\s]+)", line)
            if match:
                anr.process = match.group(1)
            anr.timestamp = line[:18] if len(line) > 18 else ""

            # 收集后续几行作为原因
            reason_lines = []
            for j in range(i + 1, min(i + 5, len(lines))):
                reason_lines.append(lines[j])
            anr.message = " ".join(reason_lines).strip()

            if not package_filter or package_filter in anr.process:
                anrs.append(anr)

    return anrs
