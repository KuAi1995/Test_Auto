"""Watch 模式 - 监听目标仓库变更，自动触发增量分析."""

import logging
import time
from pathlib import Path
from typing import Optional

from test_auto.analyzer.scanner import Analyzer
from test_auto.config.settings import Settings

logger = logging.getLogger(__name__)


class Watcher:
    """文件变更监听器（轮询模式）."""

    def __init__(self, settings: Settings, repo_name: Optional[str] = None,
                 interval: int = 30) -> None:
        self._settings = settings
        self._name = repo_name or next(iter(settings.repos), "")
        self._interval = interval
        self._repo_path = Path(settings.workspace_dir) / self._name
        self._last_mtime: dict[str, float] = {}

    def run(self) -> None:
        """启动监听循环."""
        logger.info("Watch 模式启动: %s (间隔 %ds)", self._repo_path, self._interval)
        self._scan_mtimes()

        try:
            while True:
                time.sleep(self._interval)
                changed = self._check_changes()
                if changed:
                    logger.info("检测到 %d 个文件变更，触发增量分析...", len(changed))
                    for f in changed[:5]:
                        logger.info("  变更: %s", f)
                    self._run_incremental()
                    self._scan_mtimes()
        except KeyboardInterrupt:
            logger.info("Watch 模式停止")

    def _scan_mtimes(self) -> None:
        """扫描所有 Java 文件的修改时间."""
        self._last_mtime.clear()
        for f in self._repo_path.rglob("*.java"):
            rel = str(f.relative_to(self._repo_path))
            if "/build/" not in rel:
                self._last_mtime[rel] = f.stat().st_mtime

    def _check_changes(self) -> list[str]:
        """检查变更文件."""
        changed = []
        for f in self._repo_path.rglob("*.java"):
            rel = str(f.relative_to(self._repo_path))
            if "/build/" in rel:
                continue
            mtime = f.stat().st_mtime
            if rel not in self._last_mtime or mtime > self._last_mtime[rel]:
                changed.append(rel)
        return changed

    def _run_incremental(self) -> None:
        """执行增量分析."""
        analyzer = Analyzer(self._repo_path)
        result = analyzer.analyze(incremental=True)
        if result.total_classes > 0:
            logger.info("增量分析结果: %s", result.summary())
