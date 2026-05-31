"""基线截图管理 - 版本化存储与更新."""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from test_auto.storage.database import Database

logger = logging.getLogger(__name__)


class BaselineManager:
    """基线截图管理器."""

    def __init__(self, baselines_dir: Path, db: Database) -> None:
        self._dir = baselines_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db = db

    def save_baseline(self, screenshot_path: Path, app_version: str, screen_name: str) -> Path:
        """保存基线截图.

        Args:
            screenshot_path: 源截图路径
            app_version: 应用版本
            screen_name: 页面名称

        Returns:
            基线存储路径
        """
        dest_dir = self._dir / app_version
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{screen_name}.png"

        shutil.copy2(screenshot_path, dest)

        # 写入数据库
        self._db.conn.execute(
            """INSERT OR REPLACE INTO baseline_image (app_version, screen_name, file_path, created_at)
               VALUES (?, ?, ?, ?)""",
            (app_version, screen_name, str(dest), datetime.now().isoformat()),
        )
        self._db.conn.commit()
        logger.info("基线已保存: %s/%s", app_version, screen_name)
        return dest

    def get_baseline(self, app_version: str, screen_name: str) -> Optional[Path]:
        """获取基线截图路径.

        Args:
            app_version: 应用版本
            screen_name: 页面名称

        Returns:
            基线路径，不存在返回 None
        """
        row = self._db.conn.execute(
            "SELECT file_path FROM baseline_image WHERE app_version=? AND screen_name=?",
            (app_version, screen_name),
        ).fetchone()

        if row:
            path = Path(row["file_path"])
            if path.exists():
                return path
        return None

    def list_baselines(self, app_version: Optional[str] = None) -> list[dict]:
        """列出基线截图."""
        if app_version:
            rows = self._db.conn.execute(
                "SELECT * FROM baseline_image WHERE app_version=? ORDER BY screen_name",
                (app_version,),
            ).fetchall()
        else:
            rows = self._db.conn.execute(
                "SELECT * FROM baseline_image ORDER BY app_version, screen_name"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_baseline(self, new_screenshot: Path, app_version: str, screen_name: str) -> Path:
        """更新基线（保留旧版本备份）."""
        old = self.get_baseline(app_version, screen_name)
        if old and old.exists():
            backup = old.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
            shutil.copy2(old, backup)
            logger.info("旧基线备份: %s", backup.name)

        return self.save_baseline(new_screenshot, app_version, screen_name)
