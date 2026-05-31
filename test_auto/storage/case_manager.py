"""测试用例管理 - CRUD 操作."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from test_auto.storage.database import Database

logger = logging.getLogger(__name__)


class CaseManager:
    """测试用例管理器."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def import_from_yaml(self, yaml_path: Path) -> int:
        """从 YAML 文件导入用例.

        Args:
            yaml_path: YAML 文件路径

        Returns:
            导入数量
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            cases = yaml.safe_load(f) or []

        self._db.save_test_cases(cases)
        logger.info("从 %s 导入 %d 条用例", yaml_path.name, len(cases))
        return len(cases)

    def export_to_yaml(self, output_path: Path, module: Optional[str] = None) -> int:
        """导出用例到 YAML.

        Args:
            output_path: 输出路径
            module: 按模块筛选

        Returns:
            导出数量
        """
        if module:
            rows = self._db.conn.execute(
                "SELECT * FROM test_case WHERE module=? ORDER BY id", (module,)
            ).fetchall()
        else:
            rows = self._db.conn.execute(
                "SELECT * FROM test_case ORDER BY id"
            ).fetchall()

        cases = []
        for r in rows:
            cases.append({
                "id": r["id"],
                "title": r["title"],
                "module": r["module"],
                "test_type": r["test_type"],
                "priority": r["priority"],
                "precondition": r["precondition"],
                "steps": json.loads(r["steps"]),
                "automated": bool(r["automated"]),
            })

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(cases, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info("导出 %d 条用例 → %s", len(cases), output_path)
        return len(cases)

    def list_cases(self, module: Optional[str] = None, priority: Optional[str] = None) -> list[dict]:
        """列出用例."""
        query = "SELECT * FROM test_case WHERE 1=1"
        params = []
        if module:
            query += " AND module=?"
            params.append(module)
        if priority:
            query += " AND priority=?"
            params.append(priority)
        query += " ORDER BY id"

        rows = self._db.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """获取用例统计."""
        total = self._db.conn.execute("SELECT COUNT(*) FROM test_case").fetchone()[0]
        by_priority = {}
        for row in self._db.conn.execute(
            "SELECT priority, COUNT(*) as cnt FROM test_case GROUP BY priority"
        ).fetchall():
            by_priority[row["priority"]] = row["cnt"]
        by_module = {}
        for row in self._db.conn.execute(
            "SELECT module, COUNT(*) as cnt FROM test_case GROUP BY module ORDER BY cnt DESC"
        ).fetchall():
            by_module[row["module"]] = row["cnt"]
        return {"total": total, "by_priority": by_priority, "by_module": by_module}
